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
        'environ': Map(Text(nonnull=True)),
        'path': Text(nonempty=True),
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

        curdir = runtime.curdir
        for component in profile['components']:
            buildpath = curdir / component['id']
            runtime.chdir(buildpath)
            runtime.execute('lattice.component.assemble', environ=self['environ'],
                name=component['name'], path=self['path'], specification=component,
                target=self['target'])
