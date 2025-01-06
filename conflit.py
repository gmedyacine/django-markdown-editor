dans votre script :

python
Copier le code
import subprocess

def resolve_git_conflicts(repo_path):
    """
    Resolves git merge conflicts by prioritizing incoming changes.
    """
    try:
        # Change to the repository directory
        subprocess.run(["cd", repo_path], check=True)

        # List conflicted files
        result = subprocess.run(["git", "diff", "--name-only", "--diff-filter=U"], capture_output=True, text=True)
        conflicted_files = result.stdout.splitlines()

        # Resolve each file by keeping incoming changes
        for file in conflicted_files:
            # Overwrite conflicted file with incoming changes
            subprocess.run(["git", "checkout", "--theirs", file], check=True)
            print(f"Resolved conflict in file: {file}")

        # Add resolved files
        subprocess.run(["git", "add", "."], check=True)

        # Commit the resolution
        subprocess.run(["git", "commit", "-m", "Resolved merge conflicts by keeping incoming changes"], check=True)
        print("Conflicts resolved and changes committed.")
    
    except subprocess.CalledProcessError as e:
        print(f"Error while resolving conflicts: {e}")
