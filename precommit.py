#!/usr/bin/env python
import os
import sys
import itertools
from SvnSentinel.svntransaction import SVNTransaction
from SvnSentinel.utils import *
from SvnSentinel.exceptions import RestrictedOperationException
from SvnSentinel.exceptions import AllowedOperationException


def check_restricted_paths(svn_txn, cfg):
    c = {}
    for f, txn in svn_txn.changes.iteritems():
        # append "/." for directories with property changes so they 
        # can be detected by pattern matches
        fname = os.path.join(f, ("", ".")[txn.prop_changed])
        c.setdefault(os.path.dirname(f) + "/", []).append(fname)

    blist = cfg["COMMIT_EXCEPTION_PATHS"]
    taboo_paths = cfg["NO_COMMIT_PATHS"]
    for base in c:
        d = taboo_paths.match(base)
        D = str(d) + "/"  # same thing, but with trailing "/"
        if d and (not blist[D] or not glob_filter(c[base], blist[D], len(D))):
            raise RestrictedOperationException( \
                    "Direct commits to %s is not allowed" % D, base, cfg)


def check_valid_pairs(op, src_list, dst_map, cfg):
    if op:
        src, dest = op[:2]
        valid_sources = get_matched_patterns(src, src_list)
        dst_list = [dst_map[s] for s in valid_sources]
        valid_destinations = list(set(itertools.chain(*dst_list)))  # flatten
        if get_matched_patterns(dest, valid_destinations):
            raise AllowedOperationException
        elif cfg["NO_COMMIT_PATHS"].match(dest):
            raise RestrictedOperationException( \
                    "Invalid operation on %s" % dest, dest, cfg)


def check_valid_branching(svn_txn, cfg):
    check_valid_pairs(svn_txn.is_copy_operation(),
                        cfg["VALID_BRANCH_SRCS"],
                        cfg["VALID_BRANCH_PATHS"], cfg)


def check_valid_move(svn_txn, cfg):
    check_valid_pairs(svn_txn.is_move_operation(),
                        cfg["VALID_MOVE_SRCS"],
                        cfg["VALID_MOVE_PATHS"], cfg)


def check_valid_merge(svn_txn, cfg):
    try:
        check_valid_pairs(svn_txn.is_merge_operation(),
                        cfg["VALID_MERGE_SRCS"],
                        cfg["VALID_MERGE_PATHS"], cfg)
    except AllowedOperationException:
        # TODO: more checks, e.g. check for manual edits after merge
        raise AllowedOperationException


def run_checks(cfg, repos, txn, is_revision=False):
    """
    Returns an error string if an invalid function found, else returns None.
    With the return value passed into sys.exit(), a None value translates
    into a successful exit (0) while a string value results in an errorneous
    exit (1) with the string itself written to stderr.
    """
    t = SVNTransaction(repos, txn, is_revision)
    c = cfg

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

    except RestrictedOperationException, e:
        return "%s%s" % (c["REJECT_BANNER"], e.get_message())

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
    parser.add_option("-c", "--cfg",
                    help="Configuration file to use",
                    dest="cfg_file",
                    metavar="FILE",
                    default=os.path.join(os.getcwd(), "precommit_config.py"),
                    )

    try:
        (opts, (repos, txn)) = parser.parse_args()
    except:
        return parser.print_help()

    cfg = get_config(opts.cfg_file)
    return run_checks(cfg, repos, txn, opts.revision)

if __name__ == "__main__":
    import sys
    sys.exit(main())
