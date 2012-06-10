import re
from functools import total_ordering

VERSION_EXPR = re.compile(r'^([0-9]+)[.]([0-9]+)[.]([0-9]+)(?:([a-z]{1,2})([0-9]+))?(?:[+]([0-9]+))?$')

@total_ordering
class VersionToken(object):
    SYMBOLS = ['HEAD']

    def __init__(self, version):
        if isinstance(version, VersionToken):
            version = version.version

        self.version = version
        if version in self.SYMBOLS:
            self.symbolic = True
        else:
            match = VERSION_EXPR.match(version)
            if match:
                self.symbolic = False
                self.tokens = (
                    int(match.group(1)),
                    int(match.group(2)),
                    int(match.group(3)) if match.group(3) is not None else None,
                    match.group(4),
                    int(match.group(5)) if match.group(5) is not None else None)
            else:
                raise ValueError(version)

    def __eq__(self, other):
        if not isinstance(other, VersionToken):
            try:
                other = VersionToken(other)
            except ValueError:
                return NotImplementedError()

        return other.version == self.version

    def __hash__(self):
        return hash(self.version)

    def __lt__(self, other):
        if not isinstance(other, VersionToken):
            try:
                other = VersionToken(other)
            except ValueError:
                raise NotImplementedError()

        if self.symbolic and other.symbolic:
            return self.SYMBOLS.index(self.version) < self.SYMBOLS.index(other.version)
        elif not self.symbolic and not other.symbolic:
            return self.tokens < other.tokens
        else:
            return not self.symbolic

    def __repr__(self):
        return 'VersionToken(%r)' % self.version

    def __str__(self):
        return self.version
