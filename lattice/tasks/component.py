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
        if 'INSTALLPATH' not in environ:
            environ['INSTALLPATH'] = self['path']

        return environ

class AssembleComponent(ComponentTask):
    name = 'lattice.component.assemble'
    description = 'assembles a lattice-based component'
    parameters = {
        'cachedir': Path(nonnull=True),
        'distpath': Path(nonnull=True),
        'post_tasks': Sequence(Text(nonnull=True)),
        'revision': Text(nonnull=True),
        'tarfile': Boolean(default=False),
        'url': Text(nonnull=True),
    }

    def run(self, runtime):
        component = self['specification']
        if component:
            metadata = component.get('repository')
            if not metadata:
                raise TaskError('invalid repository metadata')
        elif self['url']:
            metadata = {'url': self['url']}
            if 'git' in self['url']:
                metadata['type'] = 'git'
            if self['revision']:
                metadata['revision'] = self['revision']
        else:
            raise TaskError('repository not specified')

        distpath = self['distpath'] or runtime.curdir / 'dist'
        distpath = distpath.abspath()
        distpath.makedirs_p()

        sourcepath = uniqpath(runtime.curdir, 'src')
        repository = Repository.instantiate(metadata['type'], str(sourcepath),
            runtime=runtime, cachedir=self['cachedir'])

        repository.checkout(metadata)
        version = repository.get_current_version()

        curdir = runtime.chdir(sourcepath)
        if not component:
            component = self.component
        if component['version'] == 'HEAD':
            component['version'] = version

        original = Collation(self['path'])
        runtime.execute('lattice.component.build', name=self['name'], path=self['path'],
            target=self['target'], environ=self['environ'], specification=component)

        now = Collation(self['path']).prune(original)
        if self['tarfile']:
            environ = self.environ
            now.tar(str(distpath / '%(name)s-%(version)s.tar.bz2' % component),
                {environ['BUILDPATH']: environ['INSTALLPATH']})

        if self['post_tasks']:
            for post_task in self['post_tasks']:
                runtime.execute(post_task, environ=self['environ'], name=self['name'],
                    path=self['path'], distpath=distpath, specification=component,
                    target=self['target'], filepaths=now.filepaths)

        runtime.chdir(curdir)

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
