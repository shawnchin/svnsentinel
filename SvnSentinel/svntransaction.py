#!/usr/bin/env python
#
# Issues:
# ------
# * a copy + update shows up "A +" no "U +" in svnlook, so we can't detect
#   post-copy edits unless we follow up with a "svnlook diff --diff-copy-from"
#
# * We can detect merges by inspecting "svn:mergeinfo" on directories, but
#   manual edits after the merge will go undetected. Can we do an diff
#   to compare the transaction tree and the merge source?
#
# TODO: rewrite to use SVN Python Bindings (pysvn) instead of svnlook?
#
import re
import os
import sys
import subprocess
from operator import attrgetter


class SVNTransaction(object):
    def __init__(self, repos, txn, is_revision=False, svnlook_cmd="svnlook"):
        self.is_revision = is_revision
        self.svnlook_cmd = svnlook_cmd
        self.repos = repos
        self.txn = txn
        self._load_changes()
        self._load_info()
        #print self._svnlook("propget", "svn:mergeinfo flame2/production")

    def is_copy_operation(self):
        """Detects if this is a copy (branch/tag) operation.

        Returns a tuple of (copy_src, copy_dest) if it is, None otherwise.
        Note that the transaction must do only a copy, and not be combined
        with other operations.
        """
        if len(self.changes) == 1:
            item = self.changes.values()[0]
            if item.copied:
                return (item.source, item.path)

        return None

    def is_move_operation(self):
        """Detects if this is a move operation.

        Returns a tuple of (move_src, move_dest) if it is, None otherwise.
        Note that the transaction must do only a move, and not be combined
        with other operations.
        """
        if len(self.changes) == 2:
            s, d = sorted(self.changes.values(), key=attrgetter("copied"))
            if d.copied and s.deleted and s.path == d.source:
                return (s.path, d.path)

        return None

    def is_merge_operation(self):
        """Detects if this is a merge operation.

        Returns a tuple of (merge_src, merge_dest, src_rev) if it is a merge
        operation, or None otherwise.
        Note that the transaction must do only a merge, and not be combined
        with other operations.

        Assumes all clients have mergeinfo capabilities (should be checked
        by start-commit hook)
        """
        base = os.path.commonprefix(self.changes.keys())

        # check if property has changed in base dir
        if base not in self.changes or not self.changes[base].prop_changed:
            return None  # definitely not a merge

        # check if the mergeinfo property has changed.
        prev_rev = ""
        if self.is_revision:
            prev_rev = "-r %d" % (int(self.txn) - 1)

        mergeinfo_old = self._call("%s propget %s svn:mergeinfo %s %s" % (
                                        self.svnlook_cmd,
                                        self.repos,
                                        base,
                                        prev_rev
                                    ), exit_on_error=False)
        mergeinfo_new = self._svnlook("propget", "svn:mergeinfo %s" % base,
                                        exit_on_error=False)
        if not mergeinfo_new or mergeinfo_old == mergeinfo_new:
            return None  # mergeinfo has not changed

        # looks like a merge. Return params in the expected format
        latest_merge = mergeinfo_new.split("\n")[-1]
        src, revs = latest_merge.split(":")
        return ("%s/" % src[1:], base, revs.split("-")[-1])

    def _call(self, cmd, exit_on_error=True):
        p = subprocess.Popen(cmd.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        out, err = p.communicate()
        if err and exit_on_error:
            sys.exit("[ERROR] %s" % err)
        return out

    def _svnlook(self, subcommand="changed --copy-info",
                                        extra="", exit_on_error=True):
        r_opt = ("--transaction", "--revision")[self.is_revision]
        cmd = "%s %s %s %s %s %s" % (self.svnlook_cmd, subcommand,
                                    r_opt, self.txn, self.repos, extra)
        return self._call(cmd, exit_on_error=exit_on_error)

    def _load_changes(self):
        change_items = (SVNChangeItem(line.strip())
                            for line in re.split("\n(?=\w)", self._svnlook()))
        self.changes = dict((c.path, c) for c in change_items)

    def _load_info(self):
        self.author, self.date, _, self.log = \
                            self._svnlook("info").split("\n", 3)

    def __str__(self):
        return "%s\n%s\n%s" % (
            self.log,
            "-" * len(self.log),
            "\n".join(str(c) for c in self.changes.keys()))


class SVNChangeItem(object):
    def __init__(self, change_line):
        assert change_line[0] in "ADU_"
        assert change_line[1] in "U "
        assert change_line[2] in "+ "
        if change_line[2] == "+":
            assert change_line[0] == "A"

        self.status = change_line[0]
        self.added = (change_line[0] == "A" and change_line[2] == " ")
        self.deleted = (change_line[0] == "D")
        self.updated = (change_line[0] == "U")
        self.prop_changed = (change_line[1] == "U")
        self.copied = (change_line[2] == "+")

        self.path = change_line.split(None, 2)[-1]
        if self.copied:
            self.path, rem = self.path.split("\n", 1)
            rem = rem.strip()
            assert rem[0] == "(" and rem[-1] == ")"
            self.source, self.rev = rem[1:-1].split()[1].split(":r")

    def __str__(self):
        if self.copied:
            return "%s (copied from %s)" % (self.path, self.source)
        else:
            status_map = {
                "_": "prop-change",
                "A": "added",
                "D": "deleted",
                "U": "updated",
            }
            return "%s (%s)" % (self.path, status_map[self.status])
