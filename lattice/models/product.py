from datetime import datetime

from scheme import current_timestamp
from spire.schema import *

schema = Schema('lattice')

ProductComponents = Table('product_component', schema.metadata,
    ForeignKey(name='product_id', column='product.id', nullable=False, primary_key=True),
    ForeignKey(name='component_id', column='component.id', nullable=False, primary_key=True))

class Product(Model):
    """A product."""

    class meta:
        constraints = [UniqueConstraint('name', 'version')]
        schema = schema
        tablename = 'product'

    id = Token(segments=2, nullable=False, primary_key=True)
    name = Token(segments=1, nullable=False)
    version = Token(segments=1, nullable=False)
    status = Enumeration('supported deprecated obsolete', nullable=False,
        default='supported')
    description = Text()
    created = DateTime(timezone=True, nullable=False)

    components = relationship('Component', secondary=ProductComponents)
    dependencies = relationship('ProductDependency', backref='product',
        cascade='all,delete-orphan', passive_deletes=True)

class ProductDependency(Model):
    """A product dependency."""

    class meta:
        constraints = [UniqueConstraint('product_id', 'name')]
        schema = schema
        tablename = 'product_dependency'

    id = Identifier()
    product_id = ForeignKey('product.id', nullable=False, ondelete='CASCADE')
    name = Token(segments=1, nullable=False)
    minimum = Token(segments=1)
    maximum = Token(segments=1)
