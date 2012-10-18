import re
from uuid import uuid4

from bake import path

ENV_VAR_EXPR = re.compile(r'[$][{]([a-zA-Z]+)[}]')

def dashes_to_underscores(original):
    return dict((key.replace('-', '_'), value) for key, value in original.iteritems())

def interpolate_env_vars(content, environ):
    return ENV_VAR_EXPR.sub(lambda m: environ.get(m.group(1)), content)

def topological_sort(graph):
    queue = []
    edges = graph.values()
    for node in graph.iterkeys():
        for edge in edges:
            if node in edge:
                break
        else:
            queue.append(node)

    result = []
    while queue:
        node = queue.pop(0)
        result.append(node)
        for target in graph[node].copy():
            graph[node].remove(target)
            for edge in graph.itervalues():
                if target in edge:
                    break
            else:
                queue.append(target)

    result.reverse()
    return result

def uniqpath(root, prefix=''):
    if not isinstance(root, path):
        root = path(root)
    
    while True:
        candidate = root / ('%s%s' % (prefix, str(uuid4()).replace('-', '')[:8]))
        if not candidate.exists():
            return candidate
