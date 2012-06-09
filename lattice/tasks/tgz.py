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
        pkgname = '%s-%s.tar.bz2' % (component['name'], component['version'])

        environ = self.environ
        pattern = "',%s,%s,'" % (environ['BUILDPATH'], environ['INSTALLPATH'])

        distpath = runtime.curdir / 'dist'
        distpath.mkdir_p()

        shellargs = ['pax', '-wjvf', str(distpath / pkgname), '-s', pattern] + self['filepaths']
        runtime.shell(shellargs, merge_output=True)
