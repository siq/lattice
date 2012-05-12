from spire.mesh import ModelController
from spire.schema import SchemaDependency

from lattice.server.resources import Component as ComponentResource
from lattice.server.models import Component, ComponentRepository

class ComponentController(ModelController):
    resource = ComponentResource
    version = (1, 0)

    model = Component
    mapping = 'id name version status description timestamp'
    schema = SchemaDependency('lattice')

    def _annotate_model(self, model, data):
        repository = data.get('repository')
        if repository:
            model.repository = ComponentRepository.polymorphic_create(repository)
    
    def _annotate_resource(self, model, resource, data):
        repository = model.repository
        if repository:
            if repository.type == 'git':
                resource['repository'] = {'type': 'git', 'url': repository.url,
                    'revision': repository.revision}
            elif repository.type == 'svn':
                resource['repository'] = {'type': 'svn', 'url': repository.url}

        if data and 'include' in data and 'dependencies' in data['include']:
            resource['dependencies'] = [d.id for d in model.dependencies]
