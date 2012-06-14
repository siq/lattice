from spire.schema import *

from lattice.util import topological_sort

schema = Schema('lattice')

class Project(Model):
    """A project."""

    class meta:
        schema = schema
        tablename = 'project'

    id = Token(segments=1, nullable=False, primary_key=True)
    status = Enumeration('active inactive', nullable=False, default='active')
    description = Text()

    repository = relationship('ProjectRepository', backref='backref',
        cascade='all,delete-orphan', uselist=False)

class ProjectRepository(Model):
    class meta:
        polymorphic_on = 'type'
        schema = schema
        tablename = 'project_repository'

    id = Identifier()
    project_id = ForeignKey('project.id', nullable=False)
    type = Enumeration('git svn', nullable=False)

class GitProjectRepository(ProjectRepository):
    class meta:
        abstract = True
        polymorphic_identity = 'git'
        schema = schema

    url = Text()

ComponentDependencies = Table('component_dependency', schema.metadata,
    ForeignKey(name='component_id', column='component.id',
        nullable=False, primary_key=True),
    ForeignKey(name='dependency_id', column='component.id',
        nullable=False, primary_key=True),
)

class Component(Model):
    """A stack component."""

    class meta:
        schema = schema
        tablename = 'component'

    id = Token(segments=2, nullable=False, primary_key=True)
    name = Token(segments=1, nullable=False)
    version = Token(segments=1, nullable=False)
    status = Enumeration('active obsolete deprecated', nullable=False, default='active')
    description = Text()
    timestamp = DateTime()

    repository = relationship('ComponentRepository', backref='component',
        cascade='all,delete-orphan', uselist=False)
    builds = relationship('Build', backref='component',
        cascade='all,delete-orphan')
    dependencies = relationship('Component', secondary=ComponentDependencies,
        primaryjoin=(id == ComponentDependencies.c.component_id),
        secondaryjoin=(id == ComponentDependencies.c.dependency_id),
        backref='dependents')

    @property
    def dependency_tokens(self):
        return [dependency.id for dependency in self.dependencies]

class ComponentRepository(Model):
    class meta:
        polymorphic_on = 'type'
        schema = schema
        tablename = 'component_repository'

    id = Identifier()
    component_id = ForeignKey('component.id', nullable=False)
    type = Enumeration('git svn', nullable=False)

class GitComponentRepository(ComponentRepository):
    class meta:
        abstract = True
        polymorphic_identity = 'git'
        schema = schema

    url = Text()
    revision = Text()

class Build(Model):
    class meta:
        polymorphic_on = 'strategy'
        schema = schema
        tablename = 'component_build'
        constraints = [UniqueConstraint('component_id', 'name')]

    id = Identifier()
    component_id = ForeignKey('component.id', nullable=False)
    name = Token(segments=1, nullable=False)
    strategy = Enumeration('command script task', nullable=False)

class CommandBuild(Build):
    class meta:
        abstract = True
        polymorphic_identity = 'command'
        schema = schema

    command = Text()

class ScriptBuild(Build):
    class meta:
        abstract = True
        polymorphic_identity = 'script'
        schema = schema

    script = Text()

class TaskBuild(Build):
    class meta:
        abstract = True
        polymorphic_identity = 'task'
        schema = schema

    task = Text()

class Product(Model):
    class meta:
        schema = schema
        tablename = 'product'

    id = Token(segments=1, nullable=False, primary_key=True)
    title = Text(nullable=False)
    description = Text()

class Profile(Model):
    class meta:
        schema = schema
        tablename = 'profile'
        constraints = [UniqueConstraint('product_id', 'version')]

    id = Token(segments=2, nullable=False, primary_key=True)
    product_id = ForeignKey('product.id', nullable=False)
    version = Token(segments=1, nullable=False)

    product = relationship('Product', backref='profiles')
    components = relationship('ProfileComponent', backref='profile')

    def collate_components(self):
        graph = {}
        for component in self.components:
            graph[component] = set(component.component.dependency_tokens)

        return topological_sort(graph)

class ProfileComponent(Model):
    class meta:
        schema = schema
        tablename = 'profile_component'

    profile_id = ForeignKey('profile.id', nullable=False, primary_key=True)
    component_id = ForeignKey('component.id', nullable=False, primary_key=True)

    component = relationship('Component')
