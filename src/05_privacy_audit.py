
from pathlib import Path
import os
import re

# --------------------------------------------------
# INSIGHTPILOT - PRIVACY AND SECURITY AUDIT
# --------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

REPORT_FILE = REPORT_DIR / "privacy_audit.txt"

EXCLUDED_DIRS = {
    ".venv",
    "venv",
    ".git",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".idea",
}

TEXT_EXTENSIONS = {
    ".py", ".txt", ".md", ".csv", ".json",
    ".sql", ".toml", ".yaml", ".yml",
    ".ini", ".cfg",
}

PATTERNS = {
    "Possible email address": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    ),
    "Possible API token": re.compile(
        r"\b(?:sk-(?:proj-)?[A-Za-z0-9_-]{12,}"
        r"|gh[pousr]_[A-Za-z0-9_]{20,}"
        r"|github_pat_[A-Za-z0-9_]{20,}"
        r"|AKIA[0-9A-Z]{16})\b"
    ),
    "Windows user profile path": re.compile(
        r"[A-Za-z]:\\Users\\[^\\\s\"']+",
        re.IGNORECASE,
    ),
    "Private key": re.compile(
        r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----"
    ),
    "Possible hardcoded password": re.compile(
        r"""(?i)\bpassword\s*[:=]\s*["'][^"']{8,}["']"""
    ),
}

findings = []
screenshots = []
scanned_files = 0
skipped_files = 0

print("=" * 65)
print("INSIGHTPILOT - PRIVACY AND SECURITY AUDIT")
print("=" * 65)

# --------------------------------------------------
# CHECK GITIGNORE
# --------------------------------------------------

gitignore = ROOT / ".gitignore"

if not gitignore.exists():
    findings.append(
        "Missing .gitignore file."
    )
else:
    content = gitignore.read_text(
        encoding="utf-8"
    )

    required_rules = [
        ".venv/",
        "*.duckdb",
        ".env",
    ]

    for rule in required_rules:
        if rule not in content:
            findings.append(
                f"Missing .gitignore protection: {rule}"
            )

# --------------------------------------------------
# INSPECT PROJECT FILES
# --------------------------------------------------

for current_dir, dirs, files in os.walk(ROOT):

    dirs[:] = [
        directory
        for directory in dirs
        if directory not in EXCLUDED_DIRS
    ]

    for filename in files:

        path = Path(current_dir) / filename
        relative = path.relative_to(ROOT)
        name = filename.lower()

        if path == REPORT_FILE:
            continue

        if path.suffix.lower() in {
            ".png", ".jpg", ".jpeg", ".webp"
        }:
            screenshots.append(str(relative))
            continue

        # Detect sensitive configuration and key files
        sensitive_name = (
            (
                name.startswith(".env")
                and name != ".env.example"
            )
            or path.suffix.lower() in {
                ".pem", ".key", ".p12", ".pfx"
            }
            or name in {
                "credentials.json",
                "service_account.json",
            }
        )

        if sensitive_name:
            findings.append(
                f"Sensitive file requires review: {relative}"
            )
            continue

        if (
            path.suffix.lower() not in TEXT_EXTENSIONS
            and name != ".gitignore"
        ):
            continue

        # Avoid reading unexpectedly large files
        if path.stat().st_size > 5_000_000:
            skipped_files += 1
            continue

        try:
            lines = path.read_text(
                encoding="utf-8"
            ).splitlines()
        except (UnicodeError, OSError):
            skipped_files += 1
            continue

        scanned_files += 1

        for line_number, line in enumerate(
            lines, start=1
        ):

            for label, pattern in PATTERNS.items():

                if pattern.search(line):
                    findings.append(
                        f"{relative} | Line {line_number}"
                        f" | {label}"
                    )

# --------------------------------------------------
# GENERATE REPORT
# --------------------------------------------------

report = [
    "INSIGHTPILOT - PRIVACY AUDIT REPORT",
    "=" * 55,
    "",
    f"Text files scanned: {scanned_files}",
    f"Text files skipped: {skipped_files}",
    f"Image files identified: {len(screenshots)}",
    f"Potential issues: {len(findings)}",
    "",
]

if findings:

    report.append("REVIEW REQUIRED")
    report.append("-" * 40)

    for item in findings:
        report.append(item)

else:

    report.append(
        "No sensitive text patterns detected."
    )

report.extend([
    "",
    "MANUAL REVIEW STILL REQUIRED",
    "-" * 40,
    "1. Inspect every screenshot for private information.",
    "2. Check datasets and reports for sensitive content.",
    "3. Confirm API keys and passwords are excluded.",
    "4. Verify the exact contents of the final ZIP.",
    "5. Ensure .venv and local databases are excluded.",
    "6. Remember .gitignore does not protect ZIP files.",
    "",
    "This automated scan is not a guarantee of privacy.",
    "Potential matches are reported without secret values.",
])

REPORT_FILE.write_text(
    "\n".join(report) + "\n",
    encoding="utf-8",
)

# --------------------------------------------------
# DISPLAY SUMMARY
# --------------------------------------------------

print(f"\nText files scanned: {scanned_files}")
print(f"Text files skipped: {skipped_files}")
print(f"Image files identified: {len(screenshots)}")
print(f"Potential issues: {len(findings)}")

if findings:
    print("\nREVIEW REQUIRED:")

    for item in findings:
        print(item)
else:
    print("\nNo sensitive text patterns detected.")

print("\nManual screenshot review is still required.")
print("\nReport saved to: reports/privacy_audit.txt")

print("\nSUCCESS! PRIVACY AUDIT SCRIPT COMPLETED")
