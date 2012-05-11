from mesh.standard import *
from scheme import *

class Project(Resource):
    """A project."""

    name = 'project'
    version = 1
    requests = 'create delete get put query update'

    class schema:
        id = Token(segments=1, nonempty=True, operators='equal', oncreate=True)
        status = Enumeration('active inactive', nonnull=True, default='active',
            sortable=True, operators='equal')
        description = Text()
        repository = Structure(
            structure={
                'git': {
                    'url': Text(nonempty=True, operators='equal')},
                'svn': {
                    'url': Text(nonempty=True, operators='equal')},
            },
            polymorphic_on=Enumeration('git svn', name='type', nonnull=True, required=True))

class Component(Resource):
    """A component."""

    name = 'component'
    version = 1

    class schema:
        id = Token(segments=2, nonempty=True, operators='equal', oncreate=True,
            sortable=True)
        name = Token(segments=1, nonempty=True, operators='equal', sortable=True)
        version = Token(segments=1, nonempty=True, operators='equal', sortable=True)
        status = Enumeration('active deprecated obsolete', nonnull=True, default='active',
            sortable=True, operators='equal not in notin')
        description = Text()
        timestamp = DateTime()
        repository = Structure(
            structure={
                'git': {
                    'url': Text(nonempty=True),
                    'revision': Text(nonempty=True)},
                'svn': {
                    'url': Text(nonempty=True)},
            },
            polymorphic_on=Enumeration('git svn', name='type', nonnull=True, required=True))
        dependencies = Sequence(Token(segments=2, nonnull=True), unique=True)
