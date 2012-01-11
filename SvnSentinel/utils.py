class PathPrefixMatch(object):
    """
    Trie-based path prefix mathching utility
    
    Usage:
     path_prefixes = ("/hello/world/", "/test/")
     p = PathPrefixMatch(path_prefixes)
     p.add_path("/test2") # add another path

     p.match("/test2/drive/x.txt") # returns "/test2"
     p.match("/hello/world")  # returns "/hello/world"
     p.match("/world/domination")  # returns None
    """
    def __init__(self, paths=[], delim="/"):
        self.root = {}
        self.delim = delim

        if type(paths) in (str, unicode):
            self.add_path(paths)
        elif type(paths) in (list, tuple):
            for path in paths:
                self.add_path(path)
        else:
            raise Exception("'paths' should be of type str or list")

    def _split_path(self, path):
        if path and path[-1] == self.delim:
            path = path[:-1]  # remove trailing delimiter
        return path.split(self.delim)

    def _is_end_node(self, node):
        return node.has_key(self.delim)
            
    def _get_deepest_match(self, target):
        """
        Returns tuple of (node, depth) where node is the deepest node that
        matches the target while depth is the trie depth.
        """
        depth = 0
        node = self.root
        for s in target:
            if not node.has_key(s):
                break
            else:
                depth += 1
                node = node[s]
        return (node, depth)
        
    def add_path(self, path):
        assert type(path) is str
        if not path: return  # reject empty path
        
        segments = self._split_path(path)
        node, depth = self._get_deepest_match(segments)
        for s in segments[depth:]:
            node[s] = {}
            node = node[s]
        node[self.delim] = None  # use delim to mark end node
            
    def match(self, target):
        """
        Returns matched path if target string starts with a registered path.
        Returns None otherwise.
        """
        segments = self._split_path(target)
        node, depth = self._get_deepest_match(segments)
        if self._is_end_node(node):
            mp = self.delim.join(segments[:depth])
            return (mp, self.delim)[mp == ""]
        else:
            return None



if __name__ == "__main__":
    path_prefixes = ("/hello/world/", "/test/")
    p = PathPrefixMatch(path_prefixes)
    p.add_path("/test2") # add another path
    p.add_path("flame2/branches/")

    assert p.match("/test2/drive/x.txt") == "/test2"
    assert p.match("/hello/world/") == "/hello/world"
    assert p.match("/world/domination") == None 
    assert p.match("/world/domination") == None 
    assert p.match("flame2/branches/bugfix/b123/") == "flame2/branches"


