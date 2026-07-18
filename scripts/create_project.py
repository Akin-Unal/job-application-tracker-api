import argparse
import shutil
import sys
from pathlib import Path

EXCLUDED_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".env",
    "test.db",
}

TEXT_SUFFIXES = {
    ".env.example",
    ".ini",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yml",
    ".yaml",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a new project from this template.")
    parser.add_argument("--name", required=True, help="Human readable project name.")
    parser.add_argument("--slug", required=True, help="Repository/package slug.")
    parser.add_argument("--destination", required=True, help="Destination directory.")
    parser.add_argument("--force", action="store_true", help="Overwrite a non-empty destination.")
    return parser.parse_args()


def should_exclude(path: Path) -> bool:
    return any(part in EXCLUDED_NAMES for part in path.parts)


def copy_template(source: Path, destination: Path, force: bool) -> None:
    if destination.exists() and any(destination.iterdir()):
        if not force:
            raise RuntimeError("Destination exists and is not empty. Use --force to overwrite it.")
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    for source_path in source.rglob("*"):
        relative = source_path.relative_to(source)
        if should_exclude(relative):
            continue
        target_path = destination / relative
        if source_path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)


def replace_template_names(destination: Path, project_name: str, project_slug: str) -> None:
    replacements = {
        "Job Application Tracker API": project_name,
        "job-application-tracker-api": project_slug,
        "job_application_tracker_api": project_slug.replace("-", "_"),
        "job_application_tracker_api_db": f"{project_slug.replace('-', '_')}_db",
    }
    for path in destination.rglob("*"):
        if not path.is_file() or should_exclude(path.relative_to(destination)):
            continue
        if path.suffix not in TEXT_SUFFIXES and path.name != ".env.example":
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for old, new in replacements.items():
            content = content.replace(old, new)
        path.write_text(content, encoding="utf-8")


def print_next_steps(destination: Path, project_slug: str) -> None:
    print(f"Created project at: {destination}")
    print("")
    print("Next steps:")
    print(f"  cd {destination}")
    print("  python -m venv .venv")
    print("  .\\.venv\\Scripts\\Activate.ps1")
    print("  pip install -r requirements.txt")
    print("  Copy-Item .env.example .env")
    print("  alembic upgrade head")
    print("  uvicorn app.main:app --reload")
    print("")
    print(f"Review .env.example and Docker names for {project_slug}.")


def main() -> int:
    args = parse_args()
    source = Path(__file__).resolve().parents[1]
    destination = Path(args.destination).expanduser().resolve()
    try:
        copy_template(source, destination, args.force)
        replace_template_names(destination, args.name, args.slug)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print_next_steps(destination, args.slug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
