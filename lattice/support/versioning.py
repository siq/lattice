import re
from functools import total_ordering

VERSION_EXPR = re.compile(
    r'^([0-9]+(?:[.][0-9]+)+)'
    r'(?:([a-z]{1,2})([0-9]+))?'
    r'(?:[+]([1-9][0-9]*))?$')

PRERELEASE_TAGS = ['a', 'b', 'rc']
POSTRELEASE_TAGS = ['p']
SYMBOLIC_VERSIONS = ['HEAD']
TAGS = ['a', 'b', 'rc', 'p']

@total_ordering
class VersionToken(object):
    def __init__(self, version):
        if isinstance(version, VersionToken):
            self.version = version.version
            self.symbolic = version.symbolic
            self.tokens = version.tokens
            self.tag = version.tag
            self.epoch = version.epoch
            return

        self.version = version
        self.symbolic = False
        self.tokens = None
        self.tag = None
        self.epoch = None

        if version in SYMBOLIC_VERSIONS:
            self.symbolic = True
        else:
            self._parse_version(version)

    def __eq__(self, other):
        if not isinstance(other, VersionToken):
            try:
                other = VersionToken(other)
            except ValueError:
                return NotImplemented

        return other.version == self.version

    def __hash__(self):
        return hash(self.version)

    def __lt__(self, other):
        if not isinstance(other, VersionToken):
            try:
                other = VersionToken(other)
            except ValueError:
                return NotImplemented

        if self.symbolic and other.symbolic:
            return SYMBOLIC_VERSIONS.index(self.version) < SYMBOLIC_VERSIONS.index(other.version)
        elif self.symbolic or other.symbolic:
            return not self.symbolic
        else:
            return self._compare_version(other)

    def __repr__(self):
        if self.symbolic:
            return 'VersionToken(%r)' % self.version
        else:
            return 'VersionToken(%r, %r, %r)' % (self.tokens, self.tag, self.epoch)

    def __str__(self):
        return self.version

    @classmethod
    def validate(cls, version):
        return str(cls(version))

    def _compare_version(self, other):
        if self.tokens != other.tokens:
            return self.tokens < other.tokens

        if self.tag:
            if other.tag:
                if self.tag[0] == other.tag[0]:
                    if self.tag[1] != other.tag[1]:
                        return self.tag[1] < other.tag[1]
                else:
                    return TAGS.index(self.tag[0]) < TAGS.index(other.tag[0])
            else:
                return self.tag[0] in PRERELEASE_TAGS
        elif other.tag:
            return other.tag[0] in POSTRELEASE_TAGS

        if self.epoch and other.epoch:
            return self.epoch < other.epoch
        elif self.epoch or other.epoch:
            return self.epoch is None
        else:
            return False

    def _parse_version(self, version):
        match = VERSION_EXPR.match(version)
        if match:
            self.tokens = tuple(int(value) for value in match.group(1).split('.'))
        else:
            raise ValueError(version)
        
        tag = match.group(2)
        if tag is not None:
            if tag in PRERELEASE_TAGS or tag in POSTRELEASE_TAGS:
                self.tag = (tag, int(match.group(3)))
            else:
                raise ValueError(version)

        epoch = match.group(4)
        if epoch is not None:
            self.epoch = int(epoch)
