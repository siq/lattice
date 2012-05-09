import re

from mesh.standard import *
from scheme import *

class Component(Resource):
    """A component."""

    name = 'component'
    version = 1

    class schema:
        id = Token(segments=2, nonempty=True, operators='equal')
        name = Token(segments=1, nonempty=True, operators='equal', sortable=True)
        version = Token(segments=1, nonempty=True, operators='equal', sortable=True)
        status = Enumeration('active deprecated obsolete', nonnull=True, default='active')
        url = Text(operators='equal')
        description = Text()
        dependencies = Sequence(Token(segments=2, nonnull=True), unique=True, deferred=True)
