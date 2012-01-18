#!/usr/bin/env python
import os
import fnmatch
import itertools
from SvnSentinel.svntransaction import SVNTransaction
from SvnSentinel.utils import PathPrefixMatch

## Mechanism for bypassing commit checks
BYPASS_MESSAGE_PREFIX = "<Maintenance>"  # "None" to disallow bypass
BYPASS_ALLOWED_USERS = ("lsc", )  # "None" for no user restriction


REJECT_BANNER = """
*********************************************************************
*                SVN Sentinel : COMMIT REJECTED                     *
*********************************************************************
"""

## Shell-style wildcards supported (not regex)
# see http://docs.python.org/library/fnmatch.html

BRANCHING_PATHS = (
    ("flame2/production/", "flame2/development/"),
    ("flame2/production/", "flame2/branches/bugfix/b*/"),
    ("flame2/development/", "flame2/branches/feature/f*/"),
    ("flame2/production/", "flame2/tags/releases/*/"),
)

RELOCATION_PATHS = (
    ("flame2/development/", "flame2/tags/milestones/ms*/"),
    ("flame2/branches/bugfix/b*/", "flame2/branches/bugfix/merged/b*/"),
    ("flame2/branches/feature/f*/", "flame2/branches/feature/merged/f*/"),
    ("flame2/branches/experimental/e*/", "flame2/branches/experimental/archive/e*/"),
)

REINTEGRATION_PATHS = (
    ("flame2/branches/feature/f*", "flame2/development/"),
    ("flame2/branches/bugfix/b*", "flame2/production/"),
    ("flame2/development/", "flame2/production/"),
)

# This list is seached once for each modified file, so we need to 
# do this efficiently. A trie-based search is used. No wildcards allowed
# for blacklisted dir, but can be used for the exception list.
NO_DIRECT_COMMITS = (  
    # (blacklisted_dir, (exceptions, ...))
    ("flame2/production/", None),
    ("flame2/development/", None),
    ("flame2/tags/", None),
    ("flame2/branches/", (
            "feature/f*",
            "experimental/e*",
            "bugfix/b*",
        )),
)


class RestrictedOperationException(Exception):
    pass

class AllowedOperationException(Exception):
    pass


def get_config():
    c = {}
    c["BYPASS_MESSAGE_PREFIX"] = BYPASS_MESSAGE_PREFIX
    c["BYPASS_ALLOWED_USERS"] = BYPASS_ALLOWED_USERS
    c["REJECT_BANNER"] = REJECT_BANNER

    c["COMMIT_EXCEPTION_PATHS"] = dict(NO_DIRECT_COMMITS)  # dict to lookup exceptions
    # This list is seached once for each modified file, so we need to 
    # do this efficiently. A trie-based search is used. No wildcards allowed
    c["NO_COMMIT_PATHS"] = PathPrefixMatch(c["COMMIT_EXCEPTION_PATHS"].keys())

    def get_dict_of_lists(path_pairs):
        "store v in lists as there may be duplicate keys"
        d = {}
        for k, v in path_pairs:
            d.setdefault(k, []).append(v)
        return d
            
    c["VALID_BRANCH_PATHS"] = get_dict_of_lists(BRANCHING_PATHS)
    c["VALID_BRANCH_SRCS"] = c["VALID_BRANCH_PATHS"].keys()

    c["VALID_MOVE_PATHS"] = get_dict_of_lists(RELOCATION_PATHS)
    c["VALID_MOVE_SRCS"] = c["VALID_MOVE_PATHS"].keys()

    c["VALID_MERGE_PATHS"] = get_dict_of_lists(REINTEGRATION_PATHS)
    c["VALID_MERGE_SRCS"] = c["VALID_MERGE_PATHS"].keys()

    return c

    
def glob_filter(filenames, patterns, prefix_len=0):
    """
    Given a list of filenames and a list of patterns, return True if any of
    the files match any of the patterns.
    """
    files = filenames
    if prefix_len:
        files = [f[prefix_len:] for f in filenames]
    matched = [fnmatch.filter(files, p) for p in patterns]
    return list(set(itertools.chain(*matched)))  # return flat list with no repetitions


def get_matched_patterns(file, patterns):
    return [p for p in patterns if fnmatch.fnmatch(file, p)]

    
def check_restricted_paths(svn_txn, cfg):
    c = {}
    for f in svn_txn.changes.keys():
        c.setdefault(os.path.dirname(f) + "/", []).append(f)

    blist = cfg["COMMIT_EXCEPTION_PATHS"]
    taboo_paths = cfg["NO_COMMIT_PATHS"]
    for base in c:
        d = taboo_paths.match(base)
        D = str(d) + "/"  # same thing, but with trailing "/"
        if d and (not blist[D] or not glob_filter(c[base], blist[D], len(D))):
            raise RestrictedOperationException( \
                    "Direct commits to %s is not allowed" % d)


def check_valid_pairs(op, src_list, dst_map, cfg):
    if op:
        src, dest = op
        valid_sources = get_matched_patterns(src, src_list)
        dst_list = [dst_map[s] for s in valid_sources]
        valid_destinations =  list(set(itertools.chain(*dst_list)))  # flatten
        if get_matched_patterns(dest, valid_destinations):
            raise AllowedOperationException
        if cfg["NO_COMMIT_PATHS"].match(dest):
            raise RestrictedOperationException( \
                    "Invalid branch/move to %s" % dest)

            
def check_valid_branching(svn_txn, cfg):
    check_valid_pairs(svn_txn.is_copy_operation(),
                        cfg["VALID_BRANCH_SRCS"],
                        cfg["VALID_BRANCH_PATHS"], cfg)


def check_valid_move(svn_txn, cfg):
    check_valid_pairs(svn_txn.is_move_operation(),
                        cfg["VALID_MOVE_SRCS"],
                        cfg["VALID_MOVE_PATHS"], cfg)

                
def check_valid_merge(svn_txn, cfg):
    pass

    
def run_checks(repos, txn, is_revision=False):
    """
    Returns an error string if an invalid function found, else returns None.
    With the return value passed into sys.exit(), a None value translates
    into a successful exit (0) while a string value results in an errorneous
    exit (1) with the string itself written to stderr.
    """
    t = SVNTransaction(repos, txn, is_revision)
    c = get_config()
    
    ## Add mechanism to bypass checks
    bypass_msg = c["BYPASS_MESSAGE_PREFIX"]
    bypass_users = c["BYPASS_ALLOWED_USERS"]
    if bypass_msg and t.log.startswith(bypass_msg):
        if bypass_users is None:  # No user restriction
            return None
        assert type(bypass_users) in (list, tuple)
        if t.author in bypass_users:
            return None
    
    try:
        # check for white-listed actions
        check_valid_branching(t, c)
        check_valid_move(t, c)
        check_valid_merge(t, c)
        
        # check for blacklisted actions
        check_restricted_paths(t, c)

    except AllowedOperationException:
        return None
        
    except RestrictedOperationException as e:
        return "%s %s" % (c["REJECT_BANNER"], e.message)
        
    else:
        return None

        
def main():
    usage = """usage: %prog REPOS TXN

Run pre-commit checks on a repository transaction."""
    from optparse import OptionParser
    parser = OptionParser(usage=usage)
    parser.add_option("-r", "--revision",
                    help="Test mode. TXN actually refers to a revision.",
                    action="store_true", default=False)
    try:
        (opts, (repos, txn)) = parser.parse_args()
    except:
        return parser.print_help()
    
    return run_checks(repos, txn, opts.revision)

if __name__ == "__main__":
    import sys
    sys.exit(main())

