from tempfile import mkdtemp

from bake.path import path
from scheme import current_timestamp
from spire.schema import *
from spire.support.logs import LogHelper

from lattice.models import Component
from lattice.support.repository import Repository as RepositoryManager

__all__ = ('Repository',)

log = LogHelper('lattice')
schema = Schema('lattice')

class Repository(Model):
    """A repository."""

    class meta:
        constraints = [UniqueConstraint('domain', 'name')]
        schema = schema
        tablename = 'repository'

    id = Token(segments=2, nullable=False, primary_key=True)
    domain = ForeignKey('domain.id', nullable=False)
    name = Token(segments=1, nullable=False)
    status = Enumeration('active inactive', nullable=False, default='active')
    type = Enumeration('git svn', nullable=False)
    url = Text(nullable=False)
    created = DateTime(timezone=True, nullable=False)

    @classmethod
    def create(cls, session, **attrs):
        attrs['id'] = '%(domain)s:%(name)s' % attrs
        repository = cls(created=current_timestamp(), **attrs)

        session.add(repository)
        return repository

    def synchronize(self, session):
        tmpdir = mkdtemp()
        try:
            manager = RepositoryManager.instantiate(self.type, tmpdir)
            manager.checkout(self.url)

            for component in manager.get_components():
                try:
                    Component.put(session, **component)
                except Exception:
                    log('exception', 'synchronization of component %s failed' % component['id'])
                    session.rollback()
                else:
                    session.commit()
        finally:
            path(tmpdir).rmtree()
