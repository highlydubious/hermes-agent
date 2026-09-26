"""Operator-managed updates for installs carrying a local patch stack."""
from typing import Optional
from hermes_constants import get_default_hermes_root, get_hermes_home

def external_update_command() -> Optional[str]:
    """Prefer the current profile policy, then the machine-wide policy."""
    for home in dict.fromkeys((get_hermes_home(), get_default_hermes_root())):
        try:
            command = (home / ".external_update_command").read_text(encoding="utf-8").splitlines()[0].strip()
        except (OSError, IndexError, UnicodeError):
            continue
        if command:
            return command[:512]
    return None
