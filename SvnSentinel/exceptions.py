import fnmatch
import itertools


class AllowedOperationException(Exception):
    pass


class RestrictedOperationException(Exception):
    def __init__(self, message, dest, cfg):
        super(RestrictedOperationException, self).__init__(message)
        self._path = dest
        self._cfg = cfg

    def _match_patterns(self, valid_dst_patterns, src_map):
        matched_dest = [p for p in valid_dst_patterns
                            if fnmatch.fnmatch(self._path, p)]
        return [(s, d)
                    for d in matched_dest
                    for s in src_map[d]]

    def get_message(self):
        msg = "!! %s\n" % self.message

        no_commit = self._cfg["NO_COMMIT_PATHS"].match(self._path)
        if not no_commit:
            return msg

        rpath = "%s/" % no_commit
        elist = self._cfg["COMMIT_EXCEPTION_PATHS"][rpath]
        elist = (elist, [])[elist is None]
        excpt = ["%s%s" % (rpath, p) for p in elist]

        cp_ok = self._match_patterns(
                    self._cfg["VALID_BRANCH_DEST"],
                    self._cfg["VALID_BRANCH_PATHS_REV"])
        mv_ok = self._match_patterns(
                    self._cfg["VALID_MOVE_DEST"],
                    self._cfg["VALID_MOVE_PATHS_REV"])
        mg_ok = self._match_patterns(
                    self._cfg["VALID_MERGE_DEST"],
                    self._cfg["VALID_MERGE_PATHS_REV"])

        o = [msg]
        o.append("Changed path: %s" % self._path)
        o.append("Restricted path: %s\n" % rpath)

        if excpt or cp_ok or mv_ok or mg_ok:
            o.append("Allowed operations for this path:")
            for p in excpt:
                o.append(" - Commits to ^/%s" % p)
            for (s, d) in cp_ok:
                o.append(" - Branching from ^/%s to ^/%s" % (s, d))
            for (s, d) in mv_ok:
                o.append(" - Move from ^/%s to ^/%s" % (s, d))
            for (s, d) in mg_ok:
                o.append(" - Merge from ^/%s to ^/%s" % (s, d))

        return "\n".join(o)
