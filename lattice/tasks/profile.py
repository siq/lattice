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
        'distpath': Path(nonnull=True),
        'environ': Map(Text(nonnull=True)),
        'path': Text(nonempty=True),
        'post_tasks': Sequence(Text(nonnull=True), nonnull=True),
        'profile': Path(nonnull=True),
        'specification': Field(hidden=True),
        'target': Text(nonnull=True, default='default'),
        'build_version': Boolean(default=False),
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

        buildpath = path(self['path'])
        buildpath.mkdir()

        timestamp = datetime.utcnow()

        built = []
        for component in profile['components']:
            self._build_component(runtime, component, built, timestamp)

        if self['build_version']:
            self._build_version(runtime, profile, timestamp)

    def _build_component(self, runtime, component, built, timestamp):
        target = self['target']
        if 'builds' not in component or target not in component['builds']:
            runtime.info('ignoring %s (does not implement target %r)'
                % (component['name'], target))

        buildpath = runtime.curdir / component['name']
        buildpath.mkdir()

        curdir = runtime.chdir(buildpath)
        runtime.execute('lattice.component.assemble', environ=self['environ'],
            distpath=self['distpath'], name=component['name'], path=self['path'],
            specification=component, target=self['target'], cachedir=self['cachedir'],
            post_tasks=self['post_tasks'], built=built, timestamp=timestamp)

        runtime.chdir(curdir)

    def _build_version(self, runtime, profile, timestamp):
        """ """
        assembler = VersionComponentAssembler(profile)
        component = {'name': 'manifest', 'version': profile['version']}
        runtime.execute(
                'lattice.component.assemble', environ=self['environ'], distpath=self['distpath'],
                name=component['name'], path=self['path'],
                specification=component, target=self['target'], cachedir=self['cachedir'],
                post_tasks=self['post_tasks'], built=False, timestamp=timestamp, assembler=assembler)

class VersionComponentAssembler(ComponentAssembler):
    def __init__(self, profile):
        self.profile = profile

    def build(self, runtime, name, buildpath, target, environ, component):
        buildpath = path(buildpath)
        versionpath = buildpath / 'siq/version'
        versionpath.write_bytes(self.profile['version'])
        manifestpath = buildpath / 'siq/manifest'
        manifestpath.write_bytes('testingtesting')

    def get_version(self, component):
        return self.profile['version']

    
