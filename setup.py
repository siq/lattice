from distutils.core import setup

setup(
    name='lattice',
    version='1.0.0a1',
    description='Component registry.',
    packages=[
        'lattice',
        'lattice.server',
        'lattice.server.controllers',
        'lattice.support',
        'lattice.tasks',
    ]
)
