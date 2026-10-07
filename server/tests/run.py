import sys
import unittest
from pathlib import Path


def main() -> None:
    server = Path(__file__).resolve().parents[1]
    folder = Path(__file__).resolve().parent
    sys.path.insert(0, str(server))
    suite = unittest.defaultTestLoader.discover(start_dir=str(folder))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
