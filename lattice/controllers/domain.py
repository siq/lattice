from spire.mesh import ModelController
from spire.schema import SchemaDependency

from lattice.resources import Domain as DomainResource
from lattice.models import Domain

class DomainController(ModelController):
    resource = DomainResource
    version = (1, 0)

    model = Domain
    mapping = 'id description'
    schema = SchemaDependency('lattice')
