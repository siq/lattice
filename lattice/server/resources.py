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

Build = Structure(
    structure={
        'command': {
            'command': Text(nonempty=True),
        },
        'script': {
            'script': Text(nonempty=True),
        },
        'task': {
            'task': Text(nonempty=True),
        }
    },
    polymorphic_on=Enumeration('command script task', name='strategy', nonempty=True),
    nonnull=True)

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
        builds = Map(Build, nonnull=True)

class Product(Resource):
    """A product stack."""

    name = 'product'
    version = 1

    class schema:
        id = Token(segments=1, nonempty=True, operators='equal', oncreate=True,
            sortable=True)
        title = Text(nonempty=True)
        description = Text()

class Profile(Resource):
    """A product stack profile."""

    name = 'profile'
    version = 1

    class schema:
        id = Token(segments=2, nonempty=True, operators='equal', oncreate=True,
            sortable=True)
        product_id = Token(segments=1, nonempty=True, operators='equal', sortable=True)
        version = Token(segments=1, nonempty=True, operators='equal', sortable=True)
        product = Structure(Product.mirror_schema('id'), readonly=True)
        components = Sequence(Structure({
            'id': Token(segments=2, nonempty=True),
        }))
        sequence = Sequence(Text(), deferred=True)
