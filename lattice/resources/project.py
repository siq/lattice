from mesh.standard import *
from scheme import *

__all__ = ('Project',)

class Project(Resource):
    """A project."""

    name = 'project'
    version = 1

    class schema:
        id = Token(segments=2, operators='equal', sortable=True)
        domain = Token(segments=1, nonempty=True, operators='equal')
        name = Token(segments=1, nonempty=True, operators='equal')
        title = Text(nonempty=True)
        status = Enumeration('active inactive', nonempty=True, default='active')
        description = Text()
        created = DateTime(readonly=True, utc=True)
        repositories = Sequence(Structure({
            'id': Token(segments=2, nonempty=True),
            'status': Enumeration('active inactive', readonly=True),
            'type': Enumeration('git svn', readonly=True),
            'url': Text(readonly=True),
        }, nonnull=True), nonnull=True)
