from spire.mesh import ModelController
from spire.schema import SchemaDependency

from lattice.server.resources import Component as ComponentResource
from lattice.server.models import Build, Component, ComponentRepository

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

        builds = data.get('builds')
        if builds:
            self.schema.session.query(Build).filter(Build.component_id==model.id).delete()
            for name, build in builds.iteritems():
                build['name'] = name
                model.builds.append(Build.polymorphic_create(build))
    
    def _annotate_resource(self, model, resource, data):
        repository = model.repository
        if repository:
            resource['repository'] = repository.extract_dict(exclude=['id', 'component_id'])

        builds = resource['builds'] = {}
        for build in model.builds:
            builds[build.name] = build.extract_dict(exclude=['id', 'component_id', 'name'])

        if data and 'include' in data and 'dependencies' in data['include']:
            resource['dependencies'] = [d.id for d in model.dependencies]
