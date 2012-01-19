import os
import imp
import fnmatch
import itertools


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
        return (self.delim in node)

    def _get_deepest_match(self, target):
        """
        Returns tuple of (node, depth) where node is the deepest node that
        matches the target while depth is the trie depth.
        """
        depth = 0
        node = self.root
        for s in target:
            if s not in node:
                break
            else:
                depth += 1
                node = node[s]
        return (node, depth)

    def add_path(self, path):
        assert type(path) is str
        if path:
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


def get_dict_of_lists(path_pairs, inverse=False):
    "store v in lists as there may be duplicate keys"
    d = {}
    for k, v in path_pairs:
        if inverse:
            k, v = v, k
        d.setdefault(k, []).append(v)
    return d


def get_config(cfg_file):
    try:
        cfg_mod = imp.load_source("cfg_mod", cfg_file)
        cfg = cfg_mod.precommit_config
    except IOError:
        sys.exit("Could not load config file: %s" % cfg_file)
    except:
        sys.exit("Invalid config file: %s" % cfg_file)

    c = {}
    c["BYPASS_MESSAGE_PREFIX"] = cfg.get("BYPASS_MESSAGE_PREFIX", None)
    c["BYPASS_ALLOWED_USERS"] = cfg.get("BYPASS_ALLOWED_USERS", None)
    c["REJECT_BANNER"] = cfg.get("REJECT_BANNER", "")

    NO_DIRECT_COMMITS = cfg.get("NO_DIRECT_COMMITS", [])
    BRANCHING_PATHS = cfg.get("BRANCHING_PATHS", [])
    RELOCATION_PATHS = cfg.get("RELOCATION_PATHS", [])
    REINTEGRATION_PATHS = cfg.get("REINTEGRATION_PATHS", [])

    c["COMMIT_EXCEPTION_PATHS"] = dict(NO_DIRECT_COMMITS)

    # This list is seached once for each modified file, so we need to
    # do this efficiently. A trie-based search is used. No wildcards allowed
    c["NO_COMMIT_PATHS"] = PathPrefixMatch(c["COMMIT_EXCEPTION_PATHS"].keys())

    c["VALID_BRANCH_PATHS"] = get_dict_of_lists(BRANCHING_PATHS)
    c["VALID_BRANCH_SRCS"] = c["VALID_BRANCH_PATHS"].keys()
    c["VALID_BRANCH_PATHS_REV"] = get_dict_of_lists(BRANCHING_PATHS, True)
    c["VALID_BRANCH_DEST"] = c["VALID_BRANCH_PATHS_REV"].keys()

    c["VALID_MOVE_PATHS"] = get_dict_of_lists(RELOCATION_PATHS)
    c["VALID_MOVE_SRCS"] = c["VALID_MOVE_PATHS"].keys()
    c["VALID_MOVE_PATHS_REV"] = get_dict_of_lists(RELOCATION_PATHS, True)
    c["VALID_MOVE_DEST"] = c["VALID_MOVE_PATHS_REV"].keys()

    c["VALID_MERGE_PATHS"] = get_dict_of_lists(REINTEGRATION_PATHS)
    c["VALID_MERGE_SRCS"] = c["VALID_MERGE_PATHS"].keys()
    c["VALID_MERGE_PATHS_REV"] = get_dict_of_lists(REINTEGRATION_PATHS, True)
    c["VALID_MERGE_DEST"] = c["VALID_MERGE_PATHS_REV"].keys()

    return c


def glob_filter(filenames, patterns, prefix_len=0):
    """
    Given a list of filenames and a list of patterns, return a list of
    files that matches any of the patterns.
    """
    files = filenames
    if prefix_len:
        files = [f[prefix_len:] for f in filenames]
    matched = [fnmatch.filter(files, p) for p in patterns]
    return list(set(itertools.chain(*matched)))  # return flattened list


def get_matched_patterns(file, patterns):
    return [p for p in patterns if fnmatch.fnmatch(file, p)]


if __name__ == "__main__":
    path_prefixes = ("/hello/world/", "/test/")
    p = PathPrefixMatch(path_prefixes)
    p.add_path("/test2")  # add another path
    p.add_path("flame2/branches/")

    assert p.match("/test2/drive/x.txt") == "/test2"
    assert p.match("/hello/world/") == "/hello/world"
    assert p.match("/world/domination") == None
    assert p.match("/world/domination") == None
    assert p.match("flame2/branches/bugfix/b123/") == "flame2/branches"
