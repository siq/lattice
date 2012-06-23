from bake import path
from scheme import *

from lattice.support.versioning import VersionToken

Schema = Structure({
    'components': Sequence(Structure(nonnull=True, structure={
        'name': Token(segments=1, nonempty=True),
        'version': Token(segments=1, nonnull=True),
        'volatile': Boolean(default=False),
        'description': Text(),
        'dependencies': Sequence(Text(nonnull=True), nonnull=True),
        'builds': Map(Structure({
            'command': Text(nonnull=True),
            'script': Text(nonnull=True),
            'task': Text(nonnull=True),
            'pre-install': Text(nonnull=True),
            'post-install': Text(nonnull=True),
        }, nonnull=True), nonnull=True),
    }), nonnull=True),
})

class Specification(object):
    """A component specification."""

    DEFAULT_FILENAME = 'lattice.yaml'

    def __init__(self, version='HEAD', filename=None):
        self.components = {}
        self.filename = filename or self.DEFAULT_FILENAME
        self.version = VersionToken(version)

    def enumerate_components(self):
        for component in self.components.itervalues():
            yield component

    def get_component(self, name):
        return self.components.get(name)

    def parse(self, content, format='yaml'):
        content = Schema.unserialize(content, format)
        for component in content.get('components', []):
            if 'version' in component:
                component['version'] = VersionToken(component['version'])
            else:
                component['version'] = self.version

            component['id'] = '%(name)s:%(version)s' % component
            self.components[component['id']] = component

        return self

    def read(self, filepath='.'):
        filepath = path(filepath).abspath()
        if filepath.isdir():
            filepath /= self.filename

        content = Format.read(str(filepath))
        return self.parse(content, None)
