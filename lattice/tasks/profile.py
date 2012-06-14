from bake import *
from scheme import *

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

        built = []
        for component in profile['components']:
            self._build_component(runtime, component, built)

    def _build_component(self, runtime, component, built):
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
            post_tasks=self['post_tasks'], built=built)

        runtime.chdir(curdir)
