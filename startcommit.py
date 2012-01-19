#!/usr/bin/env python
import sys

# The start-commit hook is invoked before a Subversion txn is created
# in the process of doing a commit.  Subversion runs this hook
# by invoking a program (script, executable, binary, etc.) named
# 'start-commit' (for which this file is a template)
# with the following ordered arguments:
#
#   [1] REPOS-PATH   (the path to this repository)
#   [2] USER         (the authenticated user attempting to commit)
#   [3] CAPABILITIES (a colon-separated list of capabilities reported
#                     by the client; see note below)

err_msg = """
Your SVN client is too old and does not support merge tracking. This feature
is required for you to contribute code to this project.

Please upgrade to Subversion 1.5 or newer.
"""

if len(sys.argv) != 4:
    sys.exit("Usage: %s <REPOS-PATH> <USER> <CAPABILITIES>" % sys.argv[0])

capabilities = sys.argv[3].split(':')
if "mergeinfo" not in capabilities:
    sys.exit(err_msg)

sys.exit(0)
