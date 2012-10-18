from scheme import current_timestamp
from spire.schema import *

from lattice.models import Repository

__all__ = ('Project',)

schema = Schema('lattice')

ProjectRepositories = Table('project_repository', schema.metadata,
    ForeignKey(name='project_id', column='project.id', nullable=False, primary_key=True),
    ForeignKey(name='repository_id', column='repository.id', nullable=False, primary_key=True))

class Project(Model):
    """A project."""

    class meta:
        constraints = [UniqueConstraint('domain', 'name')]
        schema = schema
        tablename = 'project'

    id = Token(segments=2, nullable=False, primary_key=True)
    domain = ForeignKey('domain.id', nullable=False)
    name = Token(segments=1, nullable=False)
    title = Text(nullable=False)
    status = Enumeration('active inactive', nullable=False, default='active')
    description = Text()
    created = DateTime(timezone=True, nullable=False)

    repositories = relationship('Repository', secondary=ProjectRepositories)

    @classmethod
    def create(cls, session, repositories=None, **attrs):
        attrs['id'] = '%(domain)s:%(name)s' % attrs
        project = cls(created=current_timestamp(), **attrs)

        session.add(project)
        if repositories:
            for id in repositories:
                project.repositories.add(Repository.load(id=id))

        return project
