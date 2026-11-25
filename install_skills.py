"""Install the three sibling Android foldable skills; preserve existing copies."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

NAMES = (
    "android-foldable-adaptation-review",
    "android-foldable-page-capture",
    "android-foldable-design-guidelines",
)
REPO = Path(__file__).resolve().parent


def default_target():
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser() / "skills"


def verify_bundle(source):
    manifest = json.loads((REPO / "skill-set.json").read_text(encoding="utf-8"))
    if set(manifest["skills"]) != set(NAMES):
        raise ValueError("The package must contain all three skills.")
    for relative, expected in manifest["file_sha256"].items():
        path = source / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("Package file is missing or changed: " + relative)
    for name in NAMES:
        if not (source / name / "SKILL.md").is_file():
            raise ValueError("Missing skill: " + name)


def install(target):
    source = REPO / "skills" if (REPO / "skills").is_dir() else REPO
    verify_bundle(source)
    target = target.expanduser().resolve()
    if target == source.resolve() or target in source.resolve().parents or source.resolve() in target.parents:
        raise ValueError("Choose an installation directory outside this package.")
    target.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = target.parent / "skill-backups" / ("android-foldable-" + timestamp)
    changed = []
    backed_up = []
    with tempfile.TemporaryDirectory(prefix=".android-foldable-install-", dir=str(target.parent)) as staged_name:
        staged = Path(staged_name)
        for name in NAMES:
            shutil.copytree(source / name, staged / name)
        try:
            for name in NAMES:
                destination = target / name
                if destination.exists() or destination.is_symlink():
                    backup.mkdir(parents=True, exist_ok=True)
                    destination.rename(backup / name)
                    backed_up.append(name)
                (staged / name).rename(destination)
                changed.append(name)
        except Exception:
            for name in reversed(changed):
                destination = target / name
                if destination.is_dir() and not destination.is_symlink():
                    shutil.rmtree(destination)
                else:
                    destination.unlink(missing_ok=True)
            for name in reversed(backed_up):
                (backup / name).rename(target / name)
            raise
    return {
        "installed_skills": list(NAMES),
        "skills_dir": str(target),
        "backup_dir": str(backup) if backed_up else None,
        "backed_up_skills": backed_up,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=default_target(), help="Skill directory (default: CODEX_HOME/skills or ~/.codex/skills).")
    parser.add_argument("--check", action="store_true", help="Also run the installed set's dependency and rule preflight.")
    args = parser.parse_args()
    try:
        result = install(args.target)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, "Installation failed: " + str(exc) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.check:
        script = Path(result["skills_dir"]) / NAMES[0] / "scripts" / "preflight.py"
        completed = subprocess.run([sys.executable, "-B", str(script)], check=False)
        if completed.returncode:
            print("Skills are installed; fix the reported runtime dependencies before reviewing a recording.", file=sys.stderr)
            return 2
    print("Start a new Codex conversation and invoke $android-foldable-adaptation-review.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
