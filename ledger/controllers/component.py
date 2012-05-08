from spire.mesh import ModelController
from spire.schema import SchemaDependency

from ledger.resources import Component as ComponentResource
from ledger.models import Component

class ComponentController(ModelController):
    resource = ComponentResource
    version = (1, 0)

    model = Component
    mapping = 'id name version status url description'
    schema = SchemaDependency('ledger')
    
    def _annotate_resource(self, model, resource, data):
        if 'include' in data and 'dependencies' in data['include']:
            resource['dependencies'] = [d.id for d in model.dependencies]
