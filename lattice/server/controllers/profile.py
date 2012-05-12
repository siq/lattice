from spire.mesh import ModelController
from spire.schema import SchemaDependency

from lattice.server.resources import Profile as ProfileResource
from lattice.server.models import Profile, ProfileComponent

class ProfileController(ModelController):
    resource = ProfileResource
    version = (1, 0)

    model = Profile
    mapping = 'id product_id version'
    schema = SchemaDependency('lattice')

    def _annotate_model(self, model, data):
        components = data.get('components')
        if components:
            self.schema.session.query(ProfileComponent).filter(ProfileComponent.profile_id==model.id).delete()
            for component in components:
                component['component_id'] = component.pop('id')
                model.components.append(ProfileComponent(**component))

    def _annotate_resource(self, model, resource, data):
        product = model.product
        resource['product'] = {
            'title': product.title,
            'description': product.description,
        }

        components = resource['components'] = []
        for component in model.components:
            components.append({
                'id': component.component_id,
            })
