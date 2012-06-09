from bake import Task
from scheme import Sequence, Text

from lattice.tasks.component import ComponentTask

class BuildTgz(ComponentTask):
    name = 'lattice.tgz.build'
    description = 'builds a tgz of a built component'
    parameters = {
        'distpath': Path(nonempty=True),
        'filepaths': Sequence(Text(nonnull=True), nonempty=True),
    }

    def run(self, runtime):
        component = self.component
        pkgname = '%s-%s.tar.bz2' % (component['name'], component['version'])

        environ = self.environ
        pattern = ',%s,%s,' % (environ['BUILDPATH'], environ['INSTALLPATH'])

        filepath = str(self['distpath'] / pkgname)
        runtime.shell(['pax', '-wjvf', filepath, '-s', pattern] + self['filepaths'],
            merge_output=True)
