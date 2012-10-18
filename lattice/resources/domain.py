from mesh.standard import *
from scheme import *

__all__ = ('Domain',)

class Domain(Resource):
    """A domain."""

    name = 'domain'
    version = 1

    class schema:
        id = Token(segments=1, nonempty=True, oncreate=True, operators='equal')
        description = Text()
