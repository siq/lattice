from datetime import datetime

from bake import *
from scheme import *

from lattice.support.buildfile import BuildFile
from lattice.tasks.component import ComponentAssembler

class AssembleProfile(Task):
    name = 'lattice.profile.assemble'
    description = 'assembles a lattice profile'
    parameters = {
        'profile': Token(segments=2, nonempty=True),
        'path': Text(nonempty=True),

    }

class BuildProfile(Task):
    name = 'lattice.profile.build'
    description = 'builds a lattice profile'
    parameters = {
        'cachedir': Path(nonnull=True),
        'buildfile': Path(),
        'build_manifest_component': Boolean(default=False),
        'distpath': Path(nonnull=True),
        'dump_commit_log': Text(),
        'dump_manifest': Text(),
        'environ': Map(Text(nonnull=True)),
        'last_manifest': Text(),
        'existing_package_hashes': Text(),
        'override_version': Text(),
        'overwrite_existing': Boolean(default=False),
        'path': Text(nonempty=True),
        'post_tasks': Sequence(Text(nonnull=True), nonnull=True),
        'profile': Path(nonnull=True),
        'repodir': Path(nonnull=True),
        'specification': Field(hidden=True),
        'target': Text(nonnull=True, default='default'),
    }

    def run(self, runtime):
        profile = self['specification']
        if not profile:
            if self['profile']:
                content = Format.read(str(self['profile']))
                if 'profile' in content:
                    profile = content['profile']
                else:
                    raise TaskError('nope')
            else:
                raise TaskError('nope')

        if self['override_version']:
            profile['version'] = self['override_version']



        buildpath = path(self['path'])
        if buildpath.exists():
            if not self['overwrite_existing']:
                raise TaskError('buildpath already exists, aborting')
        else:
            buildpath.mkdir()

        buildfile = None
        if self['buildfile']:
            buildfile = BuildFile(self['buildfile'])

        timestamp = datetime.utcnow()
        last_manifest = self._parse_last_manifest()
        last_package_hashes = self._parse_last_manifest('package_hash')

        commit_log = None
        if self['dump_commit_log']:
            commit_log = []

        manifest = None
        if self['build_manifest_component'] or self['dump_manifest']:
            manifest = []

        built = []
        for component in profile['components']:
            starting_commit = last_manifest.get(component['name'])
            oldtarget = None
            last_package_hash = None
            if not component.get('ephemeral'):
                last_package_hash = self._existing_package(runtime, last_package_hashes.get(component['name']))
            target = self['target']
            if (('builds' in component) and (target not in component['builds'])):
                oldtarget = self['target']
                self['target'] = 'default'
            self._build_component(runtime, component, built, timestamp, manifest,
                commit_log, starting_commit, last_package_hash, buildfile)
            if oldtarget:
                self['target'] = oldtarget

        if buildfile:
            buildfile.write()
        if self['build_manifest_component'] and built:
            self._build_manifest(runtime, profile, timestamp, manifest)
        if self['dump_manifest']:
            self._dump_manifest(manifest, self['dump_manifest'])
        if self['dump_commit_log']:
            self._dump_commit_log(commit_log, self['dump_commit_log'])

    def _build_component(self, runtime, component, built, timestamp, manifest,
            commit_log, starting_commit, last_package_hash, buildfile):

        target = self['target']

        if (('builds' not in component or target not in component['builds'])
                and not component.get('ephemeral')):
            runtime.info('ignoring %s (does not implement target %r)'
                % (component['name'], target))

        assemblydir = str(runtime.curdir)
        buildpath = runtime.curdir / component['name']
        buildpath.mkdir()

        runtime.linefeed(2)
        runtime.report('***** building %s' % component['name'])

        curdir = runtime.chdir(buildpath)
        runtime.execute('lattice.component.assemble', environ=self['environ'],
            distpath=self['distpath'], name=component['name'], path=self['path'],
            specification=component, target=self['target'], cachedir=self['cachedir'],
            post_tasks=self['post_tasks'], built=built, timestamp=timestamp,
            manifest=manifest, commit_log=commit_log, starting_commit=starting_commit,
            last_package_hash=last_package_hash, repodir=self['repodir'], buildfile=buildfile,
            assemblydir=assemblydir)

        runtime.chdir(curdir)

    def _build_manifest(self, runtime, profile, timestamp, manifest):
        assembler = ManifestComponentAssembler(profile, manifest, timestamp)
        name = '%s-manifest' % profile['name']

        version = datetime.utcnow().strftime('%Y%m%d%H%M%S')

        component = {'name': name, 'version': version, 'nocache': True}
        runtime.execute('lattice.component.assemble', environ=self['environ'],
            distpath=self['distpath'], name=name, path=self['path'], specification=component,
            target=self['target'], cachedir=self['cachedir'], post_tasks=self['post_tasks'],
            built=None, timestamp=timestamp, assembler=assembler)

    def _dump_commit_log(self, commit_log, filename):
        filename = path(filename)
        filename.write_bytes('\n'.join(commit_log) + '\n')

    def _dump_manifest(self, manifest, filename):
        output = []
        for component in manifest:
            output.append('%(name)s:%(version)s:%(hash)s:%(package_hash)s' % component)

        filename = path(filename)
        filename.write_bytes('\n'.join(output) + '\n')

    def _existing_package(self, runtime, package_hash):
        if not package_hash:
            return

        filename = self['existing_package_hashes']
        if not filename:
            return 
        
        filename = path(filename)
        if not filename.exists():
            return

        res = [ line for line in filename.bytes().strip().split('\n') if line == package_hash ]

        if len(res):
            return res[0]
        else:
            return 'missing'

    def _parse_last_manifest(self, field='hash'):
        filename = self['last_manifest']
        if not filename:
            return {}

        filename = path(filename)
        if not filename.exists():
            return {}

        last_manifest = {}
        for line in filename.bytes().strip().split('\n'):
            parts = line.split(':')
            if len(parts) < 2:
                continue
            name = parts[0]
            version = parts[1]
            hash = parts[2]
            if len(parts) == 4:
                package_hash = parts[3]
            else:
                package_hash = None
            last_manifest[name] = eval(field)
        return last_manifest

class ManifestComponentAssembler(ComponentAssembler):
    def __init__(self, profile, manifest, timestamp):
        self.manifest = manifest
        self.profile = profile
        self.timestamp = timestamp

    def build(self, runtime, name, buildpath, target, environ, component):
        profile = self.profile
        buildpath = path(buildpath)

        siqdir = buildpath / 'siq'
        siqdir.mkdir_p()

        version_file = self._build_version_file()
        (buildpath / 'siq/version').write_bytes(version_file)

        manifest_file = self._build_manifest_file()
        (buildpath / 'siq/manifest').write_bytes(manifest_file)

    def get_version(self, component):
        return self.profile['version']

    def _build_manifest_file(self):
        manifest = []
        for component in self.manifest:
            manifest.append('%(name)s:%(version)s' % component)
        return '\n'.join(manifest) + '\n'

    def _build_version_file(self):
        timestamp = self.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
        return '%s (%s)\n' % (self.profile['version'], timestamp)
