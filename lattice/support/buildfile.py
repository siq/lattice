from bake import path

class BuildFile(object):
    def __init__(self, buildfile):
        if not isinstance(buildfile, path):
            buildfile = path(buildfile)

        self.buildfile = buildfile
        self.components = {}

        if self.buildfile.exists():
            for line in self.buildfile.bytes().strip().split('\n'):
                line = line.strip()
                if line:
                    component, version = line.split(' ', 1)
                    self.components[component] = version

    def get(self, component):
        return self.components.get(component)

    def set(self, component, version):
        self.components[component] = version

    def write(self):
        lines = []
        for component, version in sorted(self.components.iteritems()):
            lines.append('%s %s' % (component, version))
        self.buildfile.write_bytes('\n'.join(lines) + '\n')
