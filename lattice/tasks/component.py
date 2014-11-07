import tarfile

from bake import *
from bake.filesystem import Collation
from bake.process import Process
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
    def build(self, runtime, name, path, target, environ, component):
        pass

    def get_version(self, component):
        raise NotImplementedError()
    
    def get_rev_count(self, component):
        raise NotImplementedError()

    def populate_commit_log(self, commit_log, component, starting_commit, runtime):
        pass

    def populate_manifest(self, manifest, component):
        pass

    def prepare_source(self, runtime, component, repodir):
        pass

class StandardAssembler(ComponentAssembler):
    def build(self, runtime, name, path, target, environ, component):
        runtime.execute('lattice.component.build', name=name, path=path, target=target,
            environ=environ, specification=component)

    def get_version(self, component):
        metadata = component['repository']
        if metadata['type'] == 'svn' and metadata.has_key('revision'):
            return str(metadata.get('revision'))
        return self.repository.get_current_version()
    
    def get_rev_count(self, component):
        metadata = component['repository']
        if metadata['type'] != 'git':
            return
        return self.repository.get_rev_count()

    def populate_commit_log(self, commit_log, component, starting_commit, runtime):
        heading = '%(name)s %(version)s' % component
        metadata = component['repository']
        commit_log.append('%s\n%s\n' % (heading, '-' * len(heading)))
        commits = self.repository.get_commit_log(starting_commit)
        if commits:
            if metadata.has_key('ignore'):
                ignore = metadata.get('ignore')
                culled = str()
                block = True
                for part in commits.split('\n'):
                    if part.lower().startswith('author'):
                        author = part.split(' ')[1]
                        if author not in ignore:
                            block = False
                        else:
                            block = True
                    if block:
                        continue
                    else:
                        culled += '%s\n' % part
                commits = culled
            if commits == '':
                commits = None
        if commits:
            runtime.report('commits: %s' % commits)
            commit_log.append(commits)
            return True
        else:
            commit_log.append('no changes\n')
            return False

    def populate_manifest(self, manifest, component, last_package_hash):
        entry = {'name': component['name'], 'version': component['version']}
        entry['hash'] = self.repository.get_current_hash()
        entry['package_hash'] = last_package_hash
        exists = False
        for i, v in enumerate(manifest):
            if v['name'] == component['name']:
                exists = True
        if exists:
            manifest[i] = entry
        else: 
            manifest.append(entry)

    def prepare_source(self, runtime, component, repodir):
        try:
            metadata = component['repository']
        except KeyError:
            raise TaskError('invalid repository metadata')

        sourcepath = uniqpath(runtime.curdir, 'src')
        self.repository = Repository.instantiate(metadata['type'], str(sourcepath),
            runtime=runtime, cachedir=repodir)

        self.repository.checkout(metadata)
        return sourcepath

class AssembleComponent(ComponentTask):
    name = 'lattice.component.assemble'
    description = 'assembles a lattice-based component'
    parameters = {
        'assembler': Field(hidden=True),
        'buildfile': Field(hidden=True),
        'built': Field(hidden=True),
        'cachedir': Path(nonnull=True),
        'commit_log': Field(hidden=True),
        'distpath': Path(nonnull=True),
        'assemblydir': Field(hidden=True),
        'manifest': Field(hidden=True),
        'package_checksums': Field(hidden=True),
        'post_tasks': Sequence(Text(nonnull=True)),
        'repodir': Path(nonnull=True),
        'revision': Text(nonnull=True),
        'starting_commit': Field(hidden=True),
        'last_package_hash': Field(hidden=True),
        'tarfile': Boolean(default=False),
        'reportfile': Boolean(default=False),
        'url': Text(nonnull=True),
    }

    def run(self, runtime):
        assembler = self['assembler']
        if not assembler:
            assembler = StandardAssembler()

        component = self['specification']
 
        last_package_hash = self['last_package_hash']

        distpath = (self['distpath'] or (runtime.curdir / 'dist')).abspath()
        distpath.makedirs_p()
        
        if self['assemblydir']:
            environ = self.environ
            environ['ASSEMBLYDIR'] = self['assemblydir']
       
        curdir = assembler.prepare_source(runtime, component, self['repodir'])
        if curdir:
            curdir = runtime.chdir(curdir)

        if component['version'] == 'HEAD':
            component['version'] = assembler.get_version(component)
        elif 'p' in component['version']:
            splitchars = 'p'
            if 'pre' in component['version']: # doing this for npyscreen which has unique format
                splitchars = 'pre'
            version, pval = component['version'].split(splitchars)
            component['version'] = '%s%s%s' % (version, splitchars, (int(pval) + assembler.get_rev_count(component)))

        manifest = self['manifest']
        if manifest is not None:
            assembler.populate_manifest(manifest, component, last_package_hash)

        commit_log = self['commit_log']

        if commit_log is not None:
            has_commits = assembler.populate_commit_log(commit_log, component,
                self['starting_commit'], runtime, )
        else:
            has_commits = True
        runtime.report('has_commits: %s' % has_commits)

        built = self['built']
        if component.get('ephemeral') and not component.get('builds'):
            if built is not None and not component.get('independent') and has_commits:
                built.append(component['name'])
            if curdir:
                runtime.chdir(curdir)
            return
        
        building = self._must_build(component, built)

         # re-use existing rpm.. explode package into BUILDPATH
        if (last_package_hash and last_package_hash != 'missing') and not (has_commits or building):
            self._extract_rpm(last_package_hash)
            return

        buildfile = self['buildfile']
        cachedir = self['cachedir']

        
        if has_commits:
            building = True

        if buildfile:
            if not building:
                building = (buildfile.get(component['name']) != component['version'])
                if not building:
                    runtime.report('skipping build due to buildfile')
            buildfile.set(component['name'], component['version'])
        elif cachedir and not component.get('ephemeral') and not building:
            cachedir.makedirs_p()
            self['tarfile'] = True
            building = self._check_cachedir(cachedir, component, distpath)

        tarpath = distpath / self._get_component_tarfile(component)
        reportpath = distpath / self._get_component_reportfile(component)
        if building:
            self._run_build(runtime, assembler, component, tarpath, reportpath)
            if built is not None and not component.get('independent'):
                built.append(component['name'])

        if self['post_tasks']: # "packaging" post tasks...
            timestamp = self['timestamp']
            for post_task in self['post_tasks']:
                runtime.execute(post_task, environ=self['environ'], assembler=assembler, name=self['name'],
                    path=self['path'], distpath=distpath, specification=component,
                    target=self['target'], cachedir=cachedir, timestamp=timestamp, manifest=manifest)

        if curdir:
            runtime.chdir(curdir)
        if cachedir and not (component.get('nocache', False) or component.get('ephemeral')):
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

    def _get_component_reportfile(self, component):
        return '%(name)s-%(version)s_collation-report.txt' % component

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
            if self['branch']:
                metadata['branch'] = self['branch']
            if self['subfolder']:
                metadata['subfolder'] = self['subfolder']
            return metadata
        else:
            raise TaskError('repository not specified')

    def _must_build(self, component, built):
        if not built:
            return False

        required = []
        if 'dependencies' in component:
            required.extend(component['dependencies'])
        if 'ephemeral-dependencies' in component:
            required.extend(component['ephemeral-dependencies'])
        if not required:
            return False

        for dependency in required:
            if dependency in built:
                return True

    def _run_build(self, runtime, assembler, component, tarpath, reportpath):
        path = self['path']
        environ = self.environ

        original = Collation(path)
        assembler.build(runtime, self['name'], path, self['target'], environ, component)
        self._prune_pycpyo()
        now = Collation(path).prune(original)

        if self['tarfile']:
            now.tar(str(tarpath), {environ['BUILDPATH']: ''})
        
        if self['reportfile']:
            now.report(str(reportpath), {environ['BUILDPATH']: ''})
       
    def _extract_rpm(self, package_hash):
        environ = self.environ
        runtime = self.runtime
        curdir = runtime.curdir
        root = self.runtime.chdir(environ['BUILDPATH'])
        shellargs = ['bash', '-c', 'rpm2cpio %s/%s |cpio -idv' % (environ['STOREPATH'], package_hash)]
        runtime.shell(shellargs, merge_output=True)
        runtime.chdir(curdir)

    def _prune_pycpyo(self):
        environ = self.environ
        runtime = self.runtime
        curdir = runtime.curdir
        root = self.runtime.chdir(environ['BUILDPATH'])
        shellargs = ['bash', '-c', 'find . -type f -regex ".*\.pyc$\|.*\.pyo$"|xargs rm -fv']
        runtime.shell(shellargs, merge_output=True)
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
