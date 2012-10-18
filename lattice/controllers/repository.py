from spire.mesh import ModelController
from spire.schema import SchemaDependency

from lattice.resources import Repository as RepositoryResource
from lattice.models import Repository

class RepositoryController(ModelController):
    resource = RepositoryResource
    version = (1, 0)

    model = Repository
    mapping = 'id domain name status type url created'
    schema = SchemaDependency('lattice')
