from spire.core import Component
from spire.exceptions import TemporaryStartupError
from spire.runtime import onstartup

import lattice.models
from lattice.bundles import API

class Lattice(Component):
    api = MeshServer.deploy(bundles=[API])
