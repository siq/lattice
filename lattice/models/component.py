from datetime import datetime

from scheme import current_timestamp
from spire.schema import *
from sqlalchemy.orm.collections import attribute_mapped_collection

from lattice.util import dashes_to_underscores

__all__ = ('Component', 'ComponentBuild', 'ComponentDependency')

schema = Schema('lattice')

class Component(Model):
    """A component."""

    class meta:
        constraints = [UniqueConstraint('name', 'version')]
        schema = schema
        tablename = 'component'

    id = Token(segments=2, nullable=False, primary_key=True)
    name = Token(segments=1, nullable=False)
    version = Token(segments=1, nullable=False)
    status = Enumeration('supported deprecated obsolete', nullable=False, default='supported')
    description = Text()
    repository_id = ForeignKey('repository.id')
    revision = Text()
    created = DateTime(timezone=True, nullable=False)

    repository = relationship('Repository')
    builds = relationship('ComponentBuild', backref='component',
        collection_class=attribute_mapped_collection('name'),
        cascade='all,delete-orphan', passive_deletes=True)
    dependencies = relationship('ComponentDependency', backref='component',
        collection_class=attribute_mapped_collection('name'),
        cascade='all,delete-orphan', passive_deletes=True)

    @classmethod
    def create(cls, session, builds=None, dependencies=None, **attrs):
        if 'id' not in attrs:
            attrs['id'] = '%(name)s:%(version)s' % attrs

        component = cls(created=current_timestamp(), **attrs)
        session.add(component)

        if builds:
            for name, params in builds.iteritems():
                build = ComponentBuild(component_id=component.id, name=name, **params)
                session.add(build)

        if dependencies:
            for name, params in dependencies.iteritems():
                dependency = ComponentDependency(component_id=component.id, **params)
                session.add(dependency)

        return component

    @classmethod
    def put(cls, session, id, **attrs):
        try:
            component = cls.load(session, id=id, lockmode='update')
        except NoResultFound:
            return cls.create(session, id=id, **attrs)
        else:
            return component.update(session, **attrs)

    def update(self, session, builds=None, dependencies=None, **attrs):
        for attr, value in attrs.iteritems():
            if attr not in ('id', 'name', 'version'):
                setattr(self, attr, value)

        builds = builds or {}
        for name, build in self.builds.iteritems():
            params = builds.pop(name, None)
            if params:
                build.update_with_mapping(params)
            else:
                session.delete(build)

        for name, params in builds.iteritems():
            build = ComponentBuild(component_id=self.id, name=name, **params)
            session.add(build)

        dependencies = dependencies or {}
        for name, dependency in self.dependencies.iteritems():
            params = dependencies.pop(name, None)
            if params:
                dependency.update_with_mapping(params)
            else:
                session.delete(dependency)

        for name, params in dependencies.iteritems():
            dependency = ComponentDependency(component_id=component.id, **params)
            session.add(dependency)

        return self

class ComponentDependency(Model):
    """A component dependency."""

    class meta:
        constraints = [UniqueConstraint('component_id', 'name')]
        schema = schema
        tablename = 'component_dependency'

    id = Identifier()
    component_id = ForeignKey('component.id', nullable=False, ondelete='CASCADE')
    name = Token(segments=1, nullable=False)
    minimum = Token(segments=1)
    maximum = Token(segments=1)

class ComponentBuild(Model):
    """A component build."""

    class meta:
        constraints = [UniqueConstraint('component_id', 'name')]
        schema = schema
        tablename = 'component_build'

    id = Identifier()
    component_id = ForeignKey('component.id', nullable=False, ondelete='CASCADE')
    name = Token(segments=1, nullable=False)
    independent = Boolean(nullable=False, default=False)
    build = Text()
    preinstall = Text()
    postinstall = Text()
    preremove = Text()
    postremove = Text()
