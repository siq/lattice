import os
from collections import defaultdict
from hashlib import sha1

from bake.path import path
from bake.process import Process

from lattice.support.specification import Specification
from lattice.support.versioning import VersionToken

class Repository(object):
    implementations = {}

    def __init__(self, root, runtime=None, cachedir=None, lfile=None):
        self.cachedir = cachedir
        self.lfile = lfile or Specification.DEFAULT_FILENAME
        self.root = root
        self.runtime = runtime

    def checkout(self, metadata):
        raise NotImplementedError()

    @classmethod
    def fingerprint(cls, root=None):
        root = path(root or os.getcwd()).abspath()
        for implementation in cls.implementations.itervalues():
            if implementation.is_repository(root):
                return implementation(str(root))

    @classmethod
    def instantiate(cls, name, *args, **params):
        return cls.implementations[name](*args, **params)

    def _construct_cache_path(self, *values):
        return self.cachedir / sha1(':'.join([value or '' for value in values])).hexdigest()

class GitRepository(Repository):
    SUPPORTED_SYMBOLS = ['HEAD']

    def checkout(self, metadata):
        url = metadata['url']
        revision = metadata.get('revision')

        cached = None
        root = self.root

        if self.cachedir:
            cached = self._construct_cache_path(url, revision)
            if cached.exists():
                cached.symlink(root)
                return
            else:
                root = cached
                
        self._run_command(['clone', metadata['url'], root], False, True)
        if revision and revision != 'HEAD':
            self._run_command(['checkout', '--detach', '-q', revision],
                passthrough=True, root=root)

        if cached:
            cached.symlink(self.root)

    def enumerate_components(self):
        components = defaultdict(dict)
        for tag in self._get_tags() + self.SUPPORTED_SYMBOLS:
            specification = self._get_specification(tag)
            if specification:
                for component in specification.enumerate_components():
                    components[component['name']][component['version']] = component

        return dict(components)

    def get_component(self, name):
        specification = self._get_specification()
        if specification:
            return specification.get_component(name)

    @classmethod
    def is_repository(cls, root):
        fingerprint = root / '.git'
        return fingerprint.exists() and fingerprint.isdir()

    def _get_file(self, filename, commit=None):
        filename = '%s:%s' % (commit or 'HEAD', filename)
        try:
            return self._run_command(['show', filename]).stdout
        except RuntimeError:
            return None

    def _get_specification(self, commit='HEAD'):
        candidate = self._get_file(self.lfile, commit)
        if candidate:
            return Specification(version=commit).parse(candidate)

    def _get_tags(self):
        tags = self._run_command(['tag']).stdout.strip()
        if tags:
            return tags.split('\n')
        else:
            return []

    def _run_command(self, tokens, cwd=True, passthrough=False, root=None):
        process = Process(['git'] + tokens)
        if passthrough and self.runtime and self.runtime.verbose:
            process.merge_output = True
            process.passthrough = True

        root = root or self.root
        if process(runtime=self.runtime, cwd=root if cwd else None) == 0:
            return process
        else:
            raise RuntimeError(process.stderr or '')

Repository.implementations['git'] = GitRepository
