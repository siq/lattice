from spire.schema import *

schema = Schema('lattice')

Dependencies = Table('dependencies', schema.metadata,
    ForeignKey(name='component_id', column='components.id', nullable=False, primary_key=True),
    ForeignKey(name='dependency_id', column='components.id', nullable=False, primary_key=True),
)

class Component(Model):
    """A stack component."""

    schema = schema

    class meta:
        tablename = 'components'

    id = Token(segments=2, nullable=False, primary_key=True)
    name = Token(segments=1, nullable=False)
    version = Token(segments=1, nullable=False)
    status = Enumeration('active obsolete deprecated', nullable=False, default='active')
    url = Text()
    description = Text()

    dependencies = relationship('Component', secondary=Dependencies,
        primaryjoin=(id == Dependencies.c.component_id),
        secondaryjoin=(id == Dependencies.c.dependency_id),
        backref='dependents')
