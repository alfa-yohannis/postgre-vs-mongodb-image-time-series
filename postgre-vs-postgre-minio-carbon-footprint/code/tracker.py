from __future__ import annotations

import subprocess
import sys

from codecarbon import EmissionsTracker


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python tracker.py <project_name> <command ...>")
        raise SystemExit(1)

    project_name = sys.argv[1]
    command = sys.argv[2:]

    tracker = EmissionsTracker(
        project_name=project_name,
        output_dir="results",
        log_level="warning",
    )
    tracker.start()

    try:
        print(f"[{project_name}] Running command: {' '.join(command)}")
        subprocess.run(command, check=True)
    finally:
        tracker.stop()


if __name__ == "__main__":
    main()
