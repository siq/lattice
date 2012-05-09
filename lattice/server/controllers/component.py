from spire.mesh import ModelController
from spire.schema import SchemaDependency

from lattice.server.resources import Component as ComponentResource
from lattice.server.models import Component

class ComponentController(ModelController):
    resource = ComponentResource
    version = (1, 0)

    model = Component
    mapping = 'id name version status url description'
    schema = SchemaDependency('lattice')
    
    def _annotate_resource(self, model, resource, data):
        if 'include' in data and 'dependencies' in data['include']:
            resource['dependencies'] = [d.id for d in model.dependencies]
