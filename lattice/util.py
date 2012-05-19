from uuid import uuid4

from bake import path

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
