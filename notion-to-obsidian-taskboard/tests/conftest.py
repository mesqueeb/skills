import sys
from pathlib import Path

# Clear any 'common'/'convert' cached by another skill so we load from this one
for _mod in list(sys.modules):
    if _mod in ("common", "convert"):
        del sys.modules[_mod]

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
