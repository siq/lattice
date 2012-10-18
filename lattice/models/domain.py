from spire.schema import *

__all__ = ('Domain',)

schema = Schema('lattice')

class Domain(Model):
    """A domain."""

    class meta:
        schema = schema
        tablename = 'domain'

    id = Token(segments=1, nullable=False, primary_key=True)
    description = Text()
