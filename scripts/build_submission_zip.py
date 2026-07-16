"""Build a clean submission ZIP of the MedCloud project.

Includes only application code, documentation, tests and configuration templates.
Excludes: .git, .env, course materials / lecture transcripts, uploads, generated PDFs,
__pycache__, .pytest_cache, virtual environments, and log files.

Usage:
    python scripts/build_submission_zip.py [output_path]

If output_path is omitted, writes MedCloud_submission_<YYYYMMDD>.zip to the project root.
"""
import fnmatch
import sys
import zipfile
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Top-level entries included verbatim (subject to the exclusion patterns below).
INCLUDE_TOP_LEVEL = [
    "app",
    "docs",
    "tests",
    "scripts",
    "run.py",
    "requirements.txt",
    "pytest.ini",
    "Dockerfile",
    "docker-compose.yml",
    "render.yaml",
    ".env.example",
    ".gitignore",
    ".dockerignore",
    "README.md",
    "AGENTS.md",
]

# Directory names excluded anywhere in the tree, even inside an included top-level entry
# (e.g. app/__pycache__, tests/__pycache__) — never just at the project root.
EXCLUDE_DIR_NAMES = {
    ".git", "__pycache__", ".pytest_cache", "uploads", "generated_pdfs",
    "venv", ".venv", "env", ".idea", ".vscode", "node_modules",
    "הוראות", "תמלולי הרצאות",  # course materials / lecture transcripts — never submitted
}
EXCLUDE_FILE_PATTERNS = ["*.pyc", "*.pyo", "*.log", ".env"]


def _is_excluded_file(name: str) -> bool:
    return any(fnmatch.fnmatch(name, pattern) for pattern in EXCLUDE_FILE_PATTERNS)


def iter_files():
    """Yield every file that should go into the submission archive."""
    for entry_name in INCLUDE_TOP_LEVEL:
        entry = PROJECT_ROOT / entry_name
        if not entry.exists():
            print(f"  (skip, not found: {entry_name})")
            continue
        if entry.is_file():
            if not _is_excluded_file(entry.name):
                yield entry
            continue
        for path in entry.rglob("*"):
            if path.is_dir():
                continue
            relative_parts = path.relative_to(PROJECT_ROOT).parts
            if any(part in EXCLUDE_DIR_NAMES for part in relative_parts):
                continue
            if _is_excluded_file(path.name):
                continue
            yield path


def build_zip(output_path: Path) -> int:
    count = 0
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in iter_files():
            arcname = path.relative_to(PROJECT_ROOT)
            zf.write(path, arcname)
            count += 1
    return count


def verify_zip(output_path: Path) -> list:
    """Return a list of forbidden-looking paths found in the built archive (should be empty)."""
    forbidden = []
    with zipfile.ZipFile(output_path) as zf:
        for name in zf.namelist():
            normalized = name.replace("\\", "/")
            parts = normalized.split("/")
            if Path(name).name == ".env":
                forbidden.append(name)
            elif any(part in EXCLUDE_DIR_NAMES for part in parts):
                forbidden.append(name)
    return forbidden


def main():
    output_arg = sys.argv[1] if len(sys.argv) > 1 else None
    output_path = (
        Path(output_arg) if output_arg
        else PROJECT_ROOT / f"MedCloud_submission_{date.today():%Y%m%d}.zip"
    )

    print(f"Building submission zip -> {output_path}")
    count = build_zip(output_path)
    print(f"Wrote {count} files.")

    forbidden = verify_zip(output_path)
    if forbidden:
        print("ERROR: forbidden paths found in the archive:")
        for name in forbidden:
            print("  -", name)
        sys.exit(1)

    print(
        "Verified: no .git, .env, uploads, generated_pdfs, __pycache__, .pytest_cache, "
        "virtual environments, or course materials are present in the archive."
    )
    size_kb = output_path.stat().st_size / 1024
    print(f"Done: {output_path} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
