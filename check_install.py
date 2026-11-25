"""Check an installed Android foldable skill set without modifying it."""
import argparse
from pathlib import Path
import subprocess
import sys
from install_skills import NAMES, default_target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=default_target(), help="Directory containing the three sibling skills.")
    args = parser.parse_args()
    target = args.target.expanduser().resolve()
    missing = [name for name in NAMES if not (target / name / "SKILL.md").is_file()]
    if missing:
        parser.exit(1, "Missing installed skills: " + ", ".join(missing) + "\n")
    script = target / NAMES[0] / "scripts" / "preflight.py"
    return subprocess.run([sys.executable, "-B", str(script)], check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
