import os
from collections import defaultdict

import yaml
from bake.process import Process

from lattice.support.specification import Specification
from lattice.support.versioning import VersionToken

LATTICE_FILENAME = 'lattice.yaml'

class Repository(object):
    """A source code repository."""

    def __init__(self, path, repository):
        self.path = path
        self.repository = repository

    def enumerate_components(self):
        raise NotImplementedError()

    def prepare_repository(self):
        raise NotImplementedError()

class GitRepository(Repository):
    SUPPORTED_SYMBOLS = ['HEAD']

    def prepare_repository(self):
        self._run_command(['clone', self.repository['url'], self.path], False)

    def enumerate_components(self):
        components = defaultdict(dict)
        for tag in self._get_tags() + self.SUPPORTED_SYMBOLS:
            candidate = self._get_file(LATTICE_FILENAME, tag)
            if candidate:
                specification = Specification(version=tag).parse(candidate)
                for component in specification.enumerate_components():
                    components[component['name']][component['version']] = component

        return components

    def _get_file(self, filename, commit='HEAD'):
        filename = '%s:%s' % (commit, filename)
        try:
            return self._run_command(['show', filename]).stdout
        except RuntimeError:
            return None

    def _get_tags(self):
        tags = self._run_command(['tag']).stdout.strip()
        if tags:
            return tags.split('\n')
        else:
            return []

    def _run_command(self, tokens, cwd=True):
        cwd = self.path if cwd else None

        process = Process(['git'] + tokens)
        if process(cwd=cwd) == 0:
            return process
        else:
            raise RuntimeError(process.stderr or '')
