from spire.mesh import ModelController
from spire.schema import SchemaDependency

from lattice.server.resources import Product as ProductResource
from lattice.server.models import Product

class ProductController(ModelController):
    resource = ProductResource
    version = (1, 0)

    model = Product
    mapping = 'id title description'
    schema = SchemaDependency('lattice')
