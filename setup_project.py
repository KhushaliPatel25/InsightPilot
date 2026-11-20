
from pathlib import Path
import os
import subprocess
import sys
import venv

PROJECT_ROOT = Path(__file__).resolve().parent
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"
VENV_DIR = PROJECT_ROOT / ".venv"

if os.name == "nt":
    VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"
else:
    VENV_PYTHON = VENV_DIR / "bin" / "python"

def main():
    print("=" * 55)
    print("INSIGHTPILOT - AUTOMATIC PROJECT SETUP")
    print("=" * 55)

    print(f"\nPython version: {sys.version.split()[0]}")

    if sys.version_info[:2] != (3, 12):
        print("ERROR: Use Python 3.12 to set up InsightPilot.")
        print("In VS Code, select the Python 3.12 interpreter and run this file again.")
        sys.exit(1)

    if not REQUIREMENTS.exists():
        print("ERROR: requirements.txt was not found.")
        sys.exit(1)

    try:
        if not VENV_PYTHON.exists():
            print("\nCreating virtual environment...")
            venv.create(VENV_DIR, with_pip=True)
        else:
            print("\nVirtual environment already exists.")
            version = subprocess.run(
                [str(VENV_PYTHON), "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            if version != "3.12":
                print(f"ERROR: Existing .venv uses Python {version}, not 3.12.")
                print("Remove only the project's .venv folder and run setup again.")
                sys.exit(1)

        print("\nInstalling required libraries...")

        subprocess.run(
            [
                str(VENV_PYTHON),
                "-m",
                "pip",
                "install",
                "-r",
                str(REQUIREMENTS),
            ],
            cwd=PROJECT_ROOT,
            check=True,
        )

        print("\n" + "=" * 55)
        print("SUCCESS! INSIGHTPILOT SETUP COMPLETE")
        print("=" * 55)
        print("\nVirtual environment:", VENV_DIR)
        print("All required libraries are installed.")

    except (subprocess.CalledProcessError, OSError) as error:
        print("\nSETUP FAILED:")
        print(error)
        sys.exit(1)


if __name__ == "__main__":
    main()
