#!/usr/bin/env python
import os
from SvnSentinel.pysvnlook import SVNTransaction
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
    ("flame2/production/", "flame2/branches/bugfix/b*"),
    ("flame2/development/", "flame2/branches/feature/f*"),
    ("flame2/production/", "flame2/tags/releases/*"),
)

RELOCATION_PATHS = (
    ("flame2/development/", "flame2/tags/milestones/ms*"),
    ("flame2/branches/bugfix/b*", "flame2/branches/bugfix/merged/b*"),
    ("flame2/branches/feature/f*", "flame2/branches/feature/merged/f*"),
    ("flame2/branches/experimental/e*", "flame2/branches/experimental/archive/e*"),
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

class InvalidCommitException(Exception):
    def __init__(self, restricted_path, message=None):
        Exception.__init__(self, message)
        self.restricted_path = restricted_path


from fnmatch import filter
from itertools import chain
def glob_match(filenames, patterns, prefix_len=0):
    files = filenames
    if prefix_len:
        files = [f[prefix_len:] for f in filenames]
    matched = [filter(files, p) for p in patterns]
    return list(set(chain(*matched)))  # return flat list with no repetitions


def check_valid_branching(svn_txn):
    try:
        src, dest = svn_txn.is_copy_operation()
    except TypeError:
        return None
    d = dict(BRANCHING_PATHS)
    
        
def check_restricted_paths(svn_txn):
    c = {}
    for f in svn_txn.changes.keys():
        c.setdefault(os.path.dirname(f) + "/", []).append(f)

    # build blocklist
    blist = dict(NO_DIRECT_COMMITS)  # dict to lookup exceptions
    taboo_paths = PathPrefixMatch(blist.keys())
    for base in c:
        d = taboo_paths.match(base)
        D = str(d) + "/"  # same thing, but with trailing "/"
        if d and (not blist[D] or not glob_match(c[base], blist[D], len(D))):
            raise InvalidCommitException(d)
        
    
def run_checks(repos, txn, is_revision=False):
    """
    Returns an error string if an invalid function found, else returns None.
    With the return value passed into sys.exit(), a None value translates
    into a successful exit (0) while a string value results in an errorneous
    exit (1) with the string itself written to stderr.
    """
    t = SVNTransaction(repos, txn, is_revision)

    ## Add mechanism to bypass checks
    if BYPASS_MESSAGE_PREFIX and t.log.startswith(BYPASS_MESSAGE_PREFIX):
        if BYPASS_ALLOWED_USERS is None:  # No user restriction
            return None
        assert type(BYPASS_ALLOWED_USERS) in (list, tuple)
        if t.author in BYPASS_ALLOWED_USERS:
            return None
    
    # ---- check for white-listed actions ----
    

    # ---- check for blacklisted commits ----
    try:
        check_restricted_paths(t)
    except InvalidCommitException as e:
        return "%s Reason: Direct commits to %s is not allowed" % \
                (REJECT_BANNER, e.restricted_path)

    # ---- all other commits are considered valid ---
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

