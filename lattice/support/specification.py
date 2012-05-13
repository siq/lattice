from bake import path
from scheme import *

from lattice.support.versioning import VersionToken


Build = Structure({
    'command': Text(nonnull=True),
    'script': Text(nonnull=True),
    'task': Text(nonnull=True),
}, nonnull=True)

Schema = Structure({
    'components': Map(Structure(nonnull=True, structure={
        'version': Token(segments=1, nonnull=True),
        'description': Text(),
        'dependencies': Sequence(Text(nonnull=True), nonnull=True),
        'builds': Map(Build, nonnull=True),
    }), nonnull=True),
})

class Specification(object):
    """A lattice component specification."""

    DEFAULT_FILENAME = 'lattice.yaml'

    def __init__(self, version='HEAD'):
        self.components = {}
        self.version = VersionToken(version)

    def get_component(self, name):
        return self.components.get(name)

    def enumerate_components(self):
        for component in self.componets.itervalues():
            yield component

    def parse(self, content, format='yaml'):
        content = Schema.unserialize(content, format)
        for name, component in content.get('components', {}).iteritems():
            component['name'] = name
            if 'version' in component:
                component['version'] = VersionToken(component['version'])
            else:
                component['version'] = self.version

            component['id'] = '%(name)s:%(version)s' % component
            self.components[name] = component
        
        return self

    def read(self, filepath='.'):
        filepath = path(filepath).abspath()
        if filepath.isdir():
            filepath /= self.DEFAULT_FILENAME

        content = Format.read(str(filepath))
        return self.parse(content, None)
