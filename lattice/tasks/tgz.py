from bake import Task
from scheme import Sequence, Text

from lattice.tasks.component import ComponentTask

class BuildTgz(ComponentTask):
    name = 'lattice.tgz.build'
    description = 'builds a tgz of a built component'
    parameters = {
        'filepaths': Sequence(Text(nonnull=True), nonempty=True),
    }

    def run(self, runtime):
        component = self.component
        self.pkgname = '%s-%s.tar.bz2' % (component['name'], component['version'])

        runtime.chdir(runtime.curdir[:-len(self['name'])])
        self.filepaths = []
        [self.filepaths.append(ofilepath[len(str(runtime.curdir))+1:]) for \
                ofilepath in self['filepaths']]

        self.distpath = runtime.curdir / 'dist'
        self.distpath.mkdir()
        self._run_command(runtime)

    def _run_command(self, runtime):
        shellargs = ['pax', '-wjvf', str(self.distpath / self.pkgname), '-s', ',^,\/,']
        shellargs.extend(self.filepaths)
        runtime.shell(shellargs, environ=self['environ'], merge_output=True)

