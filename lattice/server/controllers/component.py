from spire.mesh import ModelController
from spire.schema import SchemaDependency

from lattice.server.resources import Component as ComponentResource
from lattice.server.models import Component

class ComponentController(ModelController):
    resource = ComponentResource
    version = (1, 0)

    model = Component
    mapping = 'id name version status description timestamp'
    schema = SchemaDependency('lattice')

    def _annotate_model(self, model, data):
        repository = data.get('repository')
        if repository:
            model.update(repository_type=repository['type'], repository_url=repository['url'])
            if 'revision' in repository:
                model['repository_revision'] = repository['revision']
    
    def _annotate_resource(self, model, resource, data):
        repotype = model.repository_type
        if repotype == 'git':
            resource['repository'] = {'type': 'git', 'url': model.repository_url,
                'revision': model.repository_revision}
        elif repotype == 'svn':
            resource['repository'] = {'type': 'svn', 'url': model.repository_url}

        if 'include' in data and 'dependencies' in data['include']:
            resource['dependencies'] = [d.id for d in model.dependencies]
