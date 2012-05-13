from uuid import uuid4

from bake import path

def temppath(root):
    if not isinstance(root, path):
        root = path(root)
    return root / str(uuid4()).replace('-', '')

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
