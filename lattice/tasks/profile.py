from datetime import datetime

from bake import *
from scheme import *
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
        'build_manifest_component': Boolean(default=False),
        'distpath': Path(nonnull=True),
        'environ': Map(Text(nonnull=True)),
        'override_version': Text(),
        'path': Text(nonempty=True),
        'post_tasks': Sequence(Text(nonnull=True), nonnull=True),
        'profile': Path(nonnull=True),
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
        buildpath.mkdir()

        timestamp = datetime.utcnow()

        manifest = None
        if self['build_manifest_component']:
            manifest = []

        built = []
        for component in profile['components']:
            self._build_component(runtime, component, built, timestamp, manifest)

        if self['build_manifest_component']:
            self._build_manifest(runtime, profile, timestamp, manifest)

    def _build_component(self, runtime, component, built, timestamp, manifest):
        target = self['target']
        if 'builds' not in component or target not in component['builds']:
            runtime.info('ignoring %s (does not implement target %r)'
                % (component['name'], target))

        buildpath = runtime.curdir / component['name']
        buildpath.mkdir()

        runtime.linefeed(2)
        runtime.report('***** building %s' % component['name'])

        curdir = runtime.chdir(buildpath)
        runtime.execute('lattice.component.assemble', environ=self['environ'],
            distpath=self['distpath'], name=component['name'], path=self['path'],
            specification=component, target=self['target'], cachedir=self['cachedir'],
            post_tasks=self['post_tasks'], built=built, timestamp=timestamp,
            manifest=manifest)

        runtime.chdir(curdir)

    def _build_manifest(self, runtime, profile, timestamp, manifest):
        assembler = ManifestComponentAssembler(profile, manifest)
        name = '%s-manifest' % profile['name']

        component = {'name': name, 'version': profile['version'], 'nocache': True}
        runtime.execute('lattice.component.assemble', environ=self['environ'],
            distpath=self['distpath'], name=name, path=self['path'], specification=component,
            target=self['target'], cachedir=self['cachedir'], post_tasks=self['post_tasks'],
            built=None, timestamp=timestamp, assembler=assembler)

class ManifestComponentAssembler(ComponentAssembler):
    def __init__(self, profile, manifest):
        self.profile = profile
        self.manifest = manifest

    def build(self, runtime, name, buildpath, target, environ, component):
        profile = self.profile
        buildpath = path(buildpath)

        versionpath = buildpath / 'siq/version'
        versionpath.write(profile['version'])

        manifest = []
        for component in self.manifest:
            manifest.append('%(name)s %(version)s' % component)

        manifestpath = buildpath / 'siq/manifest'
        manifestpath.write_bytes('\n'.join(manifest))

    def get_version(self, component):
        return self.profile['version']

    
