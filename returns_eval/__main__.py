import sys

if sys.version_info < (3, 9):  # checked before importing anything else, for a clear message
    sys.exit("This project needs Python 3.9 or newer. You have " + sys.version.split()[0] + ".")

from .cli import main  # noqa: E402

sys.exit(main())
