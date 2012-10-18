import re

from bake import path
from scheme import *

from lattice.support.versioning import VersionToken

WHITESPACE = re.compile(r'\s+')

Build = Structure({
    'independent': Boolean(default=False),
    'build': Text(nonnull=True),
    'preinstall': Text(nonnull=True),
    'postinstall': Text(nonnull=True),
    'preremove': Text(nonnull=True),
    'postremove': Text(nonnull=True),
}, nonnull=True)

Schema = Structure({
    'components': Sequence(Structure({
        'name': Token(segments=1, nonempty=True),
        'version': Token(segments=1, nonnull=True),
        'description': Text(),
        'dependencies': Sequence(Text(nonnull=True), nonnull=True),
        'builds': Map(Build, nonnull=True),
    }, nonnull=True), nonnull=True),
}, strict=False)

class Specification(object):
    """A project specification."""

    DEFAULT_FILENAME = 'lattice.yaml'
    DEFAULT_VERSION = 'HEAD'

    def __init__(self, version=None, filename=None):
        self.components = {}
        self.filename = filename or self.DEFAULT_FILENAME
        self.version = VersionToken(version or self.DEFAULT_VERSION)

    def enumerate_components(self):
        for component in self.components.itervalues():
            yield component

    def get_component(self, name):
        return self.components.get(name)
    
    def parse(self, content, format='yaml'):
        content = Schema.unserialize(content, format)
        for component in content.get('components', []):
            self._parse_component(component)
            self.components[component['id']] = component

        return self

    def read(self, filepath='.'):
        filepath = path(filepath).abspath()
        if filepath.isdir():
            filepath /= self.filename

        content = Format.read(str(filepath))
        return self.parse(content, None)

    def _parse_component(self, component):
        if 'version' in component:
            component['version'] = VersionToken(component['version'])
        else:
            component['version'] = self.version

        dependencies = {}
        if 'dependencies' in component:
            for dependency in component['dependencies']:
                dependency = self._parse_dependency(dependency)
                if dependency['name'] not in dependencies:
                    dependencies[dependency['name']] = dependency
                else:
                    raise ValueError('duplicate dependency')

        component['dependencies'] = dependencies
        component['id'] = '%(name)s:%(version)s' % component

    def _parse_dependency(self, dependency):
        tokens = WHITESPACE.sub(' ', dependency).strip().split(' ')
        if not tokens:
            raise ValueError(dependency)

        value = {'name': tokens.pop(0), 'minimum': None, 'maximum': None}
        while tokens:
            operator = tokens.pop(0)
            if operator in ('>=', '<='):
                if tokens:
                    version = VersionToken.validate(tokens.pop(0))
                else:
                    raise ValueError(dependency)
            elif len(operator) > 2:
                operator, version = operator[:2], operator[2:]
                if operator in ('>=', '<='):
                    version = VersionToken.validate(version)
                else:
                    raise ValueError(dependency)
            else:
                raise ValueError(dependency)

            if operator == '>=':
                if value['minimum'] is None:
                    value['minimum'] = version
                else:
                    raise ValueError(dependency)
            elif operator == '<=':
                if value['maximum'] is None:
                    value['maximum'] = version
                else:
                    raise ValueError(dependency)

        return value
