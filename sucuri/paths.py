"""Path confinement shared by the compiler and the server.

Template and request supplied paths must never resolve outside the directory they
belong to, so every join goes through one checked helper instead of repeating the
comparison at each call site.
"""

import os


def resolve_within(base_dir, path, extension=None):
    """Resolve ``path`` under ``base_dir``, returning None if it escapes.

    Symlinks are resolved before the check, so a link pointing outside is refused
    too.
    """
    if not path:
        return None
    if extension and not path.endswith(extension):
        path += extension
    base_root = os.path.realpath(base_dir)
    full_path = os.path.realpath(os.path.join(base_root, path))
    if full_path != base_root and not full_path.startswith(base_root + os.sep):
        return None
    return full_path
