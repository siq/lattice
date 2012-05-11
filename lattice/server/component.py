from mesh.standard import Bundle, mount
from spire.core import Component
from spire.mesh import MeshServer

import lattice.server.models
from lattice.server import resources

bundle = Bundle('lattice',
    mount(resources.Component, 'lattice.server.controllers.component.ComponentController'),
    mount(resources.Project, 'lattice.server.controllers.project.ProjectController'),
)

class Lattice(Component):
    api = MeshServer.deploy(
        bundles=[bundle],
        path='/api')
