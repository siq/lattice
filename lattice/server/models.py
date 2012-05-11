from spire.schema import *

schema = Schema('lattice')

class Project(Model):
    """A project."""

    schema = schema
    class meta:
        tablename = 'project'

    id = Token(segments=1, nullable=False, primary_key=True)
    status = Enumeration('active inactive', nullable=False, default='active')
    description = Text()

    repository = relationship('ProjectRepository', backref='project', cascade='all,delete-orphan',
        uselist=False)

class ProjectRepository(Model):
    schema = schema
    class meta:
        tablename = 'project_repository'
        polymorphic_on = 'type'
        

    id = Identifier()
    project_id = ForeignKey('project.id', nullable=False)
    type = Enumeration('git svn', nullable=False)

class GitProjectRepository(ProjectRepository):
    schema = schema
    class meta:
        abstract = True
        polymorphic_identity = 'git'
        extend_existing = True

    url = Text(nullable=False)

ComponentDependencies = Table('component_dependency', schema.metadata,
    ForeignKey(name='component_id', column='component.id', nullable=False, primary_key=True),
    ForeignKey(name='dependency_id', column='component.id', nullable=False, primary_key=True),
)

class Component(Model):
    """A stack component."""

    schema = schema

    class meta:
        tablename = 'component'

    id = Token(segments=2, nullable=False, primary_key=True)
    name = Token(segments=1, nullable=False)
    version = Token(segments=1, nullable=False)
    status = Enumeration('active obsolete deprecated', nullable=False, default='active')
    description = Text()
    timestamp = DateTime()

    repository = relationship('ComponentRepository', backref='component',
        cascade='all,delete-orphan', uselist=False)

    dependencies = relationship('Component', secondary=ComponentDependencies,
        primaryjoin=(id == ComponentDependencies.c.component_id),
        secondaryjoin=(id == ComponentDependencies.c.dependency_id),
        backref='dependents')

class ComponentRepository(Model):
    schema = schema
    class meta:
        tablename = 'component_repository'
        polymorphic_on = 'type'

    id = Identifier()
    component_id = ForeignKey('component.id', nullable=False)
    type = Enumeration('git svn', nullable=False)

class GitComponentRepository(ComponentRepository):
    schema = schema
    class meta:
        abstract = True
        polymorphic_identity = 'git'
        extend_existing = True

    url = Text(nullable=False)
    revision = Text(nullable=False)
