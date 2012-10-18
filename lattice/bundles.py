from mesh.standard import Bundle, mount

from lattice.resources import *

API = Bundle('lattice',
    mount(Domain, 'lattice.controllers.domain.DomainController'),
    mount(Repository, 'lattice.controllers.repository.RepositoryController'),
)
