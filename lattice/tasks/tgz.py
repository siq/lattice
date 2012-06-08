from bake import *
from bake.filesystem import Collation
from scheme import *

from lattice.support.repository import Repository
from lattice.support.specification import Specification
from lattice.util import uniqpath

class BuildTgz(Task):
    name = 'lattice.tgz.build'
    description = 'builds a tgz of a built component'
    parameters = {
        'environ': Map(Text(nonnull=True), description='environment for the build'),
        'name': Text(description='name of the component to build', nonempty=True),
        'specification': Field(hidden=True),
        'filepaths': Sequence(item=Text(nonnull=True),nonnull=True),
    }

    def run(self, runtime):
        component = self['specification']
        if not component:
            specification = Specification().read()
            component = specification.get_component(self['name'])
            if not component:
                raise TaskError('unknown component')

        if 'builds' not in component:
            raise TaskError('component has no builds')
        
        environ = self['environ']
        if environ is None:
            environ = {}

        self.pkgname = '%s-%s.tar.bz2' % (self['name'], component['version'])
        runtime.chdir(runtime.curdir[:-len(self['name'])])
        self.filepaths = []
        [self.filepaths.append(ofilepath[len(str(runtime.curdir))+1:]) for \
                ofilepath in self['filepaths']]
        self.distpath = runtime.curdir / 'dist'
        self.distpath.mkdir()
        self._run_command(runtime, environ)

    def _run_command(self, runtime, environ):
        shellargs = ['pax', '-wjvf', str(self.distpath / self.pkgname), '-s', ',^,\/,']
        shellargs.extend(self.filepaths)
        runtime.shell(shellargs, environ=environ, merge_output=True)
