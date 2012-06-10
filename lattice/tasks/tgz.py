from bake import *
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
        pkgbasename = '%s-%s' % (component['name'], component['version'])

        environ = self.environ
        pattern = ',%s,%s,' % (environ['BUILDPATH'], environ['INSTALLPATH'])

        filepath = str(self['distpath'] / pkgbasename) + '.tar'
        runtime.shell(['pax', '-wvf', filepath, '-s', pattern] + self['filepaths'],
                merge_output=True)

        runtime.shell(['bzip2', filepath], merge_output=True)
