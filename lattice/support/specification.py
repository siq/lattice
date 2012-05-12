from scheme import *

from lattice.support.versioning import VersionToken

Schema = Structure({
    'components': Map(Structure({
        'version': Token(segments=1, nonnull=True),
        'description': Text(),
        'dependencies': Sequence(Token(segments=1, nonnull=True), nonnull=True, unique=True),
        'builds': Map(Structure({
            'script': Text(nonempty=True)
        })),
    })),
})

class Specification(object):
    def __init__(self, name=None, version=None):
        self.components = {}
        self.name = name
        self.version = VersionToken(version) if version else None

    def enumerate_components(self):
        for component in self.components.itervalues():
            yield component

    def parse(self, content, format='yaml'):
        content = Schema.unserialize(content, format)
        
        for name, component in content.get('components', {}).iteritems():
            component['name'] = name
            if 'version' in component:
                component['version'] = VersionToken(component['version'])
            elif self.version:
                component['version'] = self.version
            else:
                raise Exception()
            self.components[name] = component

        return self
