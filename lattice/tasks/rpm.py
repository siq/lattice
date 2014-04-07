from bake import *
import tarfile
from bake.util import get_package_data
from scheme import *

from lattice.tasks.component import ComponentTask
from lattice.util import interpolate_env_vars

class BuildRpm(ComponentTask):
    name = 'lattice.rpm.build'
    description = 'builds a rpm file of a built component'
    parameters = {
        'cachedir': Path(nonnull=True),
        'distpath': Path(nonempty=True),
        'prefix': Text(nonnull=True),
    }

    SCRIPTS = (
        ('pre-install', 'pre-install-script', 'pre'),
        ('post-install', 'post-install-script', 'post'),
        ('pre-remove', 'pre-remove-script', 'preun'),
        ('post-remove', 'post-remove-script', 'postun'),
    )

    def run(self, runtime):
        component = self.component
        environ = self.environ

        name = component['name']
        version = component['version']
        self.tgzname = '%s-%s.tar.bz2' % (name, version)
        self.reportpath = path('%s/%s-%s_collation-report.txt' % (str(self['distpath']), name, version))

        prefix = self['prefix']
        if prefix:
            name = '%s-%s' % (prefix.strip('-'), name)

        # supplement for rpm's release req
        self.release = component.get('release')
        if self.release:
            self.release = int(self.release) + 1
        elif component.get('volatile'):
            timestamp = self['timestamp']
            if timestamp:
                self.release = timestamp.strftime('%Y%m%d%H%M%S')
        else:
            self.release = 1

        # supplement for arch value
        self.arch = 'x86_64'

        self.pkgname = '%s-%s-%s.%s.rpm' % (name, version, self.release, self.arch)

        self.workpath = runtime.curdir / ('build_%s_rpm' % name)
        self.workpath.makedirs_p()

        self.specdir = self.workpath / 'SPECS'
        self.buildrootdir = self.workpath / 'BUILDROOT'
        self.builddir = self.workpath / 'BUILD'

        self.specdir.mkdir_p()
        self.buildrootdir.mkdir_p()
        self.builddir.mkdir_p()

        dependencies = component.get('dependencies')
        if dependencies:
            if prefix:
                dependencies = ['%s-%s' % (prefix.strip('-'), d) for d in dependencies]
            dependencies = ', '.join(dependencies)

        template = get_package_data('lattice', 'templates/rpm-spec-file.tmpl')
        specfile = template % {
            'component_name': name,
            'component_version': version,
            'component_release': self.release,
            'component_maintainer_name': 'IBM',
            'component_maintainer_email': 'storediqsupport@us.ibm.com',
            'component_depends': dependencies or 'siq-appstack',
            'component_description': 'Package generated by lattice.rpm.build'}

        self.specpath = path('%s/%s-%s.spec' % (str(self.specdir), name, version)) 
        self.specpath.write_bytes(specfile)

        try:
            build = self.build
        except TaskError:
            build = {}

        for file_token, script_token, script_name in self.SCRIPTS:
            script = None
            if file_token in build:
                scriptpath = path(build[file_token])
                if scriptpath.exists():
                    speccontent = ['\n', '%%%s' % script_name]
                    speccontent.extend(scriptpath.lines()[1:])
                    scriptpath.write_lines(speccontent)
                    script = scriptpath.bytes()
            elif script_token in build:
                script = build[script_token]
            if script:
                script = interpolate_env_vars(script, environ)
                self.specpath.write_bytes(script, append=True)


        runtime.chdir(self.buildrootdir)
        self._run_tar(runtime)
        membersfile = self.builddir / 'INSTALLED_FILES'
        membersfile.write_lines(self.membernames, append=True)


        self.specpath.write_text('%files -f INSTALLED_FILES\n', append=True)

        runtime.chdir(self.workpath)
        self._run_rpmbuild(runtime)

    def _run_tar(self, runtime):
        shellargs = ['tar', '-xjf', str(self['distpath'] / self.tgzname)]
        runtime.shell(shellargs, merge_output=True)
        opentar = tarfile.open(str(self['distpath'] / self.tgzname), 'r')
        self.membernames = ['\"/' + name + '\"' for name in opentar.getnames()]

    def _run_rpmbuild(self, runtime):
        pkgpath = self['distpath'] / self.arch / self.pkgname
        runtime.shell(['fakeroot', 'rpmbuild', '-bb', 
                       '--define', ' _rpmdir %s' % str(self['distpath']), 
                       '--define', '_topdir %s' % str(self.workpath), str(self.specpath),
                       '--buildroot', self.buildrootdir],
                      merge_output=True)

        cachedir = self['cachedir']
        if cachedir:
            pkgpath.copy2(cachedir)

