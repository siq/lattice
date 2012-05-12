from mesh.standard import Bundle, mount
from spire.core import Component
from spire.mesh import MeshServer

import lattice.server.models
from lattice.server import resources

bundle = Bundle('lattice',
    mount(resources.Component, 'lattice.server.controllers.component.ComponentController'),
    mount(resources.Product, 'lattice.server.controllers.product.ProductController'),
    mount(resources.Profile, 'lattice.server.controllers.profile.ProfileController'),
    mount(resources.Project, 'lattice.server.controllers.project.ProjectController'),
)

class Lattice(Component):
    api = MeshServer.deploy(
        bundles=[bundle],
        path='/api')
