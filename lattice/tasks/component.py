import tarfile

from bake import *
from bake.filesystem import Collation
from scheme import *

from lattice.support.repository import Repository
from lattice.support.specification import Specification
from lattice.util import uniqpath

class ComponentTask(Task):
    parameters = {
        'environ': Map(Text(nonnull=True), description='environment for the build'),
        'name': Text(nonempty=True),
        'path': Text(description='build path', nonempty=True),
        'specification': Field(hidden=True),
        'target': Text(nonnull=True, default='default'),
        'timestamp': Field(hidden=True),
    }

    @property
    def build(self):
        component = self.component
        if 'builds' not in component:
            raise TaskError('invalid build target')

        build = component['builds'].get(self['target'])
        if build:
            return build
        else:
            raise TaskError('invalid build target')

    @property
    def component(self):
        component = self['specification']
        if not component:
            specification = Specification().read()
            component = specification.get_component(self['name'])
            if not component:
                raise TaskError('unknown component')
        return component

    @property
    def environ(self):
        environ = self['environ']
        if environ is None:
            environ = {}

        environ['BUILDPATH'] = self['path']
        return environ

class ComponentAssembler(object):
    def __init__(self, component):
        self.component = component

    def build(self, runtime, name, path, target, environ, component):
        pass

    def get_version(self):
        raise NotImplementedError()

    def prepare_source(self, runtime, sourcepath, repodir):
        pass

class StandardAssembler(ComponentAssembler):
    def build(self, runtime, name, path, target, environ, component):
        runtime.execute('lattice.component.build', name=name, path=path, target=target,
            environ=environ, specification=component)

    def get_version(self):
        return self.repository.get_current_version()

    def prepare_source(self, runtime, sourcepath, repodir):
        try:
            metadata = self.component['repository']
        except KeyError:
            raise TaskError('invalid repository metadata')

        self.repository = Repository.instantiate(metadata['type'], str(sourcepath),
            runtime=runtime, cachedir=repodir)
        self.repository.checkout(metadata)

class AssembleComponent(ComponentTask):
    name = 'lattice.component.assemble'
    description = 'assembles a lattice-based component'
    parameters = {
        'assembler': Field(hidden=True, default=StandardAssembler),
        'built': Field(hidden=True),
        'cachedir': Path(nonnull=True),
        'distpath': Path(nonnull=True),
        'post_tasks': Sequence(Text(nonnull=True)),
        'repodir': Path(nonnull=True),
        'revision': Text(nonnull=True),
        'tarfile': Boolean(default=False),
        'url': Text(nonnull=True),
    }

    def run(self, runtime):
        component = self['specification']
        assembler = self['assembler'](component)
        environ = self.environ

        distpath = ((self['distpath'] or runtime.curdir) / 'dist').abspath()
        distpath.makedirs_p()

        sourcepath = uniqpath(runtime.curdir, 'src')
        assembler.prepare_source(runtime, sourcepath, self['repodir'])

        version = assembler.get_version()
        if component['version'] == 'HEAD':
            component['version'] = version

        curdir = runtime.chdir(sourcepath)
        built = self['built']
        building = self._must_build(component, built)

        cachedir = self['cachedir']
        if cachedir:
            cachedir.makedirs_p()
            self['tarfile'] = True
            if not building:
                building = self._check_cachedir(cachedir, component, distpath)
        else:
            building = True

        tarpath = distpath / self._get_component_tarfile(component)
        if building:
            self._run_build(runtime, assembler, component, tarpath)
            if built is not None and not component.get('independent'):
                built.append(component['name'])

        if self['post_tasks']:
            timestamp = self['timestamp']
            for post_task in self['post_tasks']:
                runtime.execute(post_task, environ=self['environ'], name=self['name'],
                    path=self['path'], distpath=distpath, specification=component,
                    target=self['target'], cachedir=cachedir, timestamp=timestamp)

        runtime.chdir(curdir)
        if cachedir:
            tarpath.copy2(cachedir)

    def _check_cachedir(self, cachedir, component, distpath):
        cached = cachedir / self._get_component_tarfile(component)
        if cached.exists():
            cached.copy2(distpath)
        else:
            return True

        openfile = tarfile.open(cached, 'r')
        try:
            openfile.extractall(str(self['path']))
        finally:
            openfile.close()

    def _get_component_tarfile(self, component):
        return '%(name)s-%(version)s.tar.bz2' % component

    def _get_repository_metadata(self, component):
        if component:
            try:
                return component['repository']
            except KeyError:
                raise TaskError('invalid repository metadata')
        elif self['url']:
            metadata = {'url': self['url']}
            if 'git' in self['url']:
                metadata['type'] == 'git'
            if self['revision']:
                metadata['revision'] = self['revision']
            return metadata
        else:
            raise TaskError('repository not specified')

    def _must_build(self, component, built):
        if not built:
            return False

        dependencies = component.get('dependencies')
        if not dependencies:
            return False

        for dependency in dependencies:
            if dependency in built:
                return True

    def _run_build(self, runtime, assembler, component, tarpath):
        path = self['path']
        environ = self.environ

        original = Collation(path)
        assembler.build(runtime, self['name'], path, self['target'], environ, component)
        now = Collation(path).prune(original)

        if self['tarfile']:
            now.tar(str(tarpath), {environ['BUILDPATH']: ''})

class BuildComponent(ComponentTask):
    name = 'lattice.component.build'
    description = 'builds a lattice-based component'

    def run(self, runtime):
        build = self.build
        if 'command' in build:
            self._run_command(runtime, build)
        elif 'script' in build:
            self._run_script(runtime, build)
        elif 'task' in build:
            self._run_task(runtime, build)

    def _run_command(self, runtime, build):
        runtime.shell(build['command'], environ=self.environ, merge_output=True)

    def _run_script(self, runtime, build):
        script = uniqpath(runtime.curdir, 'script')
        script.write_bytes(build['script'])

        runtime.shell(['bash', '-x', script], environ=self.environ, merge_output=True)
        script.unlink()
