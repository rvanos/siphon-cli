
import fnmatch
import os

from siphon.cli.constants import IGNORE_PATHS, SIPHON_IGNORE

def get_ignored():
    # Try loading from a .siphonignore file. If this doesn't exist,
    # use the default ignored files from the constants file.
    lines = set()
    try:
        with open(SIPHON_IGNORE, 'r') as f:
            for line in iter(f.readline, ''):
                if line[0] != '#' and line.rstrip('\n'):
                    l = line.strip().rstrip('\n')
                    try:
                        comment_start = l.index('#')
                        lines.add(l[0:comment_start].strip())
                    except ValueError:
                        lines.add(l)
    except:
        pass
    lines.update(set(IGNORE_PATHS))
    return list(lines)

def keep(names, ignore_patterns=None, prefix=''):
    """
    Given a list of file names and ignore patterns, keep returns a list of
    those paths that we want to keep.

    The ignore patterns specify absolute paths unless the pattern contains
    and asterisk. In this case we check for matches using the fnmatch module.
    """
    if not ignore_patterns:
        ignore_patterns = get_ignored()

    # Create the paths we want to filter
    if prefix:
        paths = [os.path.join(prefix, p) for p in names]
    else:
        paths = names

    fnmatch_patterns = [p for p in ignore_patterns if '*' in p]
    absolute_patterns = list(set(ignore_patterns) - set(fnmatch_patterns))

    # We can immediately remove absolute_patterns from the paths
    candidates = list(set(paths) - set(absolute_patterns))

    filtered = candidates
    for p in fnmatch_patterns:
        filtered = list(set(filtered) - set(fnmatch.filter(filtered, p)))

    return [os.path.relpath(f, prefix) for f in filtered]
