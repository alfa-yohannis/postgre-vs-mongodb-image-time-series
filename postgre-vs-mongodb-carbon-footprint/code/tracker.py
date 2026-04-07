import sys
import subprocess
from codecarbon import EmissionsTracker

def main():
    if len(sys.argv) < 3:
        print("Usage: python tracker.py <project_name> <command_script>")
        sys.exit(1)
        
    project_name = sys.argv[1]
    command = sys.argv[2:]

    # Start CodeCarbon Tracker
    tracker = EmissionsTracker(
        project_name=project_name, 
        output_dir="results",
        log_level="warning"
    )
    tracker.start()

    try:
        print(f"[{project_name}] Running command: {' '.join(command)}")
        # Execute the command
        subprocess.run(command, check=True)
    finally:
        # Stop Tracker
        tracker.stop()

if __name__ == "__main__":
    main()
