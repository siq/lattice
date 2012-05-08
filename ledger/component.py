from mesh.standard import Bundle, mount
from spire.core import Component
from spire.mesh import MeshServer

import ledger.models
from ledger import resources

bundle = Bundle('ledger',
    mount(resources.Component, 'ledger.controllers.component.ComponentController'),
)

class Ledger(Component):
    api = MeshServer.deploy(
        bundles=[bundle],
        path='/api')
