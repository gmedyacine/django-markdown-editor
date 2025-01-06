import subprocess
import os

def resolve_git_conflicts(repo_path):
    """
    Resolves git merge conflicts by prioritizing incoming changes.
    """
    if not os.path.exists(repo_path):
        print(f"Error: Repository path does not exist: {repo_path}")
        return

    try:
        print(f"Changing to repository path: {repo_path}")

        # List conflicted files
        print("Listing conflicted files...")
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=U"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        conflicted_files = result.stdout.splitlines()
        if not conflicted_files:
            print("No conflicts detected.")
            return

        print(f"Conflicted files detected: {conflicted_files}")

        # Resolve each file by keeping incoming changes
        for file in conflicted_files:
            print(f"Resolving conflict for file: {file}")
            subprocess.run(["git", "checkout", "--theirs", file], cwd=repo_path, check=True)

        # Add resolved files
        print("Adding resolved files...")
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)

        # Commit the resolution
        print("Committing resolved conflicts...")
        subprocess.run(
            ["git", "commit", "-m", "Resolved merge conflicts by keeping incoming changes"],
            cwd=repo_path,
            check=True
        )
        print("Conflicts resolved and changes committed successfully.")
    
    except subprocess.CalledProcessError as e:
        print(f"Error during Git operation: {e}")
        print(f"Command: {e.cmd}")
        print(f"Return code: {e.returncode}")
        print(f"Output: {e.output}")
        print(f"Error output: {e.stderr}")
    except Exception as e:
        print(f"Unexpected error: {e}")

# Call the function with the repository path
resolve_git_conflicts("/mnt/domino/repo_path")
