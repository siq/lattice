from scheme import Map, Sequence, Text
from bake import Task

class BuildTgz(Task):
    name = 'lattice.tgz.build'
    description = 'builds a tgz of a built component'
    parameters = {
        'environ': Map(Text(nonnull=True), description='environment for the build'),
        'name': Text(description='name of the component to build', nonempty=True),
        'filepaths': Sequence(item=Text(nonnull=True),nonnull=True),
        'version': Text(description='version of the component to package', nonempty=True)
    }

    def run(self, runtime):
        environ = self['environ']
        self.pkgname = '%s-%s.tar.bz2' % (self['name'], self['version'])
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

