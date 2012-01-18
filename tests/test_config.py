c = precommit_config = {}

## Banner to display along with the error message on commit rejection
c["REJECT_BANNER"] = """
*********************************************************************
*                SVN Sentinel : COMMIT REJECTED                     *
*********************************************************************
"""

## Allow commits to bypass checks if it the commit message starts with
## a specific text. Defaults to None (disable bypass mechanism)
c["BYPASS_MESSAGE_PREFIX"] = "<Maintenance>" 

## If bypass mechanism is enable, limit it to a list of authorised
## users. Defaults to None (no user restrictions)
c["BYPASS_ALLOWED_USERS"] = None  


## Specifies list of paths that are blacklist, i.e. changes cannot be
## committed to unless the path is covered by the exclusion list or
## if the operation has been whitelisted.
##
## This list is seached once for each modified file, so we need to
## do this efficiently. A trie-based search is used.
##
## No wildcards allowed for blacklisted dir, but can be used for the
## exception list.
c["NO_DIRECT_COMMITS"] = (
    # (blacklisted_dir, (exceptions, ...))
    ("production/", None),
    ("development/", None),
    ("tags/", None),
    ("branches/", (
            "feature/f[0-9]*/?*",
            "experimental/e[0-9]*/?*",
            "bugfix/b[0-9]*/?*",
        )),
)

## Whitelisted branching paths. If not whitelisted, branch operations
## that write into restricted paths will be rejected.
## Note that whitelisting only applies if the branch/copy if the
## only operation performed in the commit.
## Shell-style wildcards (not regex) can be used in paths
## see http://docs.python.org/library/fnmatch.html
c["BRANCHING_PATHS"] = (
    ("production/", "development/"),
    ("production/", "branches/bugfix/b[0-9]*/"),
    ("development/", "branches/feature/f[0-9]*/"),
    ("production/", "tags/releases/*/"),
)

## Whitelisted move paths. If not whitelisted, move operations
## that write into restricted paths will be rejected.
## Note that whitelisting only applies if the move is the
## only operation performed in the commit.
## Shell-style wildcards (not regex) can be used in paths
## see http://docs.python.org/library/fnmatch.html
c["RELOCATION_PATHS"] = (
    ("development/", "tags/milestones/ms[0-9]*/"),
    ("branches/bugfix/b[0-9]*/", "branches/bugfix/merged/b[0-9]*/"),
    ("branches/feature/f[0-9]*/", "branches/feature/merged/f[0-9]*/"),
    ("branches/experimental/e[0-9]*/", "branches/experimental/archive/e[0-9]*/"),
)

## Whitelisted merge paths. If not whitelisted, merge operations
## that write into restricted paths will be rejected.
## Note that whitelisting only applies if the merge is the
## only operation performed in the commit.
## Shell-style wildcards (not regex) can be used in paths
## see http://docs.python.org/library/fnmatch.html
c["REINTEGRATION_PATHS"] = (
    ("branches/feature/f[0-9]*/", "development/"),
    ("branches/bugfix/b[0-9]*/", "production/"),
    ("development/", "production/"),
)


