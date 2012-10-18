from mesh.standard import *
from scheme import *

__all__ = ('Repository',)

class Repository(Resource):
    """A repository."""

    name = 'repository'
    version = 1

    class schema:
        id = Token(segments=2, operators='equal')
        domain = Token(segments=1, nonempty=True, operators='equal')
        name = Token(segments=1, nonempty=True, operators='equal')
        status = Enumeration('active inactive', nonempty=True, default='active')
        type = Enumeration('git svn', nonempty=True)
        url = Text(nonempty=True)
        created = DateTime(utc=True, readonly=True)
