## Mechanism for bypassing commit checks

c = precommit_config = {}

c["BYPASS_MESSAGE_PREFIX"] = "<Maintenance>"  # "None" to disallow bypass
c["BYPASS_ALLOWED_USERS"] = ("lsc", )  # "None" for no user restriction


c["REJECT_BANNER"] = """
*********************************************************************
*                SVN Sentinel : COMMIT REJECTED                     *
*********************************************************************
"""

## Shell-style wildcards supported (not regex)
# see http://docs.python.org/library/fnmatch.html

c["BRANCHING_PATHS"] = (
    ("flame2/production/", "flame2/development/"),
    ("flame2/production/", "flame2/branches/bugfix/b*/"),
    ("flame2/development/", "flame2/branches/feature/f*/"),
    ("flame2/production/", "flame2/tags/releases/*/"),
)

c["RELOCATION_PATHS"] = (
    ("flame2/development/", "flame2/tags/milestones/ms*/"),
    ("flame2/branches/bugfix/b*/", "flame2/branches/bugfix/merged/b*/"),
    ("flame2/branches/feature/f*/", "flame2/branches/feature/merged/f*/"),
    ("flame2/branches/experimental/e*/", "flame2/branches/experimental/archive/e*/"),
)

c["REINTEGRATION_PATHS"] = (
    ("flame2/branches/feature/f*", "flame2/development/"),
    ("flame2/branches/bugfix/b*", "flame2/production/"),
    ("flame2/development/", "flame2/production/"),
)

# This list is seached once for each modified file, so we need to 
# do this efficiently. A trie-based search is used. No wildcards allowed
# for blacklisted dir, but can be used for the exception list.
c["NO_DIRECT_COMMITS"] = (  
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