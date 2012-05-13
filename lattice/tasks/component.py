from bake import *
from bake.filesystem import Collation
from scheme import *

from lattice.support.repository import Repository
from lattice.support.specification import Specification
from lattice.util import temppath

class AssembleComponent(Task):
    name = 'lattice.component.assemble'
    description = 'assembles a lattice-based component'
    parameters = {
        'name': Text(required=True),
        'path': Text(description='build path', required=True),
        'build': Text(description='build target', default='default'),
        'specification': Field(hidden=True, required=True),
        'collate': Boolean(default=False),
    }

    def run(self, runtime):
        component = self['specification']
        if not component:
            raise TaskError('invalid component')

        metadata = component.get('repository')
        if not metadata:
            raise TaskError('invalid repository metadata')

        sourcepath = runtime.curdir / 'src'
        if sourcepath.exists():
            sourcepath.rmtree()

        repository = Repository.instantiate(metadata['type'], str(sourcepath),
            runtime=runtime)
        repository.checkout(metadata)

        original = None
        if self['collate']:
            original = Collation(self['path'])

        curdir = runtime.chdir(sourcepath)
        runtime.execute('lattice.component.build', name=self['name'], path=self['path'],
            build=self['build'], specification=component)
        runtime.chdir(curdir)

        if self['collate']:
            now = Collation(self['path']).prune(original)
            now.report(curdir / 'collation.txt')

class BuildComponent(Task):
    name = 'lattice.component.build'
    description = 'builds a lattice-based component'
    parameters = {
        'name': Text(description='name of the component to build', required=True),
        'path': Text(description='target path', required=True),
        'build': Text(description='name of build target', default='default'),
        'specification': Field(hidden=True),
    }

    def run(self, runtime):
        component = self['specification']
        if not component:
            specification = Specification().read()
            component = specification.get_component(self['name'])
            if not component:
                raise TaskError('unknown component')

        if 'builds' not in component:
            raise TaskError('component has no builds')

        build = component['builds'].get(self['build'])
        if not build:
            raise TaskError('invalid build target')

        environ = {'BUILDROOT': self['path']}
        if 'command' in build:
            self._run_command(runtime, environ, build)
        elif 'script' in build:
            self._run_script(runtime, environ, build)
        elif 'task' in build:
            self._run_task(runtime, environ, build)

    def _run_command(self, runtime, environ, build):
        runtime.shell(build['command'], environ=environ, merge_output=True)

    def _run_script(self, runtime, environ, build):
        tempfile = temppath(runtime.curdir)
        tempfile.write_bytes(build['script'])

        runtime.shell(['bash', '-x', tempfile], environ=environ, merge_output=True)
        tempfile.unlink()
