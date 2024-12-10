import git
import os
import shutil

# Configuration
URL_GITLAB = "https://gitlab.example.com/group/repo.git"  # Remplacez par l'URL réelle du dépôt GitLab
USERID = "your_user_id"                                   # Remplacez par votre identifiant GitLab
TOKEN = "your_access_token"                               # Remplacez par votre token GitLab
LOCAL_REPO_DIR = "/tmp/gitlab_repo"                      # Répertoire temporaire pour le clone du dépôt
SOURCE_FILE = "PROD/migration.csv"                       # Chemin du fichier source dans le dépôt
TARGET_FILE = "/home/migration-tools/migration.csv"      # Chemin cible où le fichier sera copié

def clone_or_pull_repo():
    """Clone le dépôt si le répertoire local n'existe pas, sinon fait un pull pour mettre à jour."""
    if os.path.exists(LOCAL_REPO_DIR):
        print("Le dépôt existe déjà. Mise à jour avec git pull...")
        repo = git.Repo(LOCAL_REPO_DIR)
        origin = repo.remotes.origin
        origin.pull()
    else:
        print("Clonage du dépôt...")
        auth_url = URL_GITLAB.replace("https://", f"https://{USERID}:{TOKEN}@")
        repo = git.Repo.clone_from(auth_url, LOCAL_REPO_DIR)
    return repo

def copy_file():
    """Copie le fichier migration.csv du dépôt vers le chemin cible."""
    source_path = os.path.join(LOCAL_REPO_DIR, SOURCE_FILE)
    if os.path.exists(source_path):
        os.makedirs(os.path.dirname(TARGET_FILE), exist_ok=True)
        shutil.copy2(source_path, TARGET_FILE)
        print(f"Fichier copié avec succès vers {TARGET_FILE}")
    else:
        print(f"Erreur : Le fichier source {source_path} est introuvable.")

def main():
    try:
        repo = clone_or_pull_repo()
        copy_file()
    except Exception as e:
        print(f"Une erreur est survenue : {e}")

if __name__ == "__main__":
    main()
