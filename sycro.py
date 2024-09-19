import os
import subprocess
import json
import zipfile
from datetime import datetime

# Chemins des répertoires
project_dir = "/tmp/test-synchro/projet-test"
blob_store_dir = "/path/to/blob/store"  # Remplace par le chemin vers les blobs binaires

# Fonction pour exécuter une commande Git
def execute_git_command(command, cwd=project_dir):
    subprocess.run(command, shell=True, check=True, cwd=cwd)

# Fonction pour extraire un fichier binaire du blob store
def extract_file_from_blob(content_hash, target_file):
    # Les deux premières lettres du contentHash définissent le sous-dossier
    subdir = content_hash[:2]
    blob_path = os.path.join(blob_store_dir, subdir, content_hash)
    
    if os.path.exists(blob_path):
        # Si c'est un ZIP, on l'extrait
        if blob_path.endswith(".zip"):
            with zipfile.ZipFile(blob_path, 'r') as zip_ref:
                zip_ref.extractall(os.path.dirname(target_file))
            print(f"Extrait {target_file} depuis {blob_path}")
        else:
            # Si ce n'est pas un ZIP, on copie simplement le fichier
            with open(blob_path, 'rb') as src, open(target_file, 'wb') as dest:
                dest.write(src.read())
            print(f"Copié {target_file} depuis {blob_path}")
    else:
        print(f"Blob introuvable: {blob_path}")
        return False
    return True

# Fonction pour traiter et reconstruire les commits
def process_commits():
    # Lister les commits dans l'ordre inverse pour garder l'historique
    commit_list = subprocess.check_output('git rev-list --all', shell=True, cwd=project_dir).decode('utf-8').splitlines()
    
    for commit in reversed(commit_list):  # Parcours dans l'ordre chronologique
        # Checkout du commit
        execute_git_command(f'git checkout {commit}')
        
        # Parcourir les fichiers du commit
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                if file.endswith('.py'):  # Exemple pour les fichiers à traiter
                    file_path = os.path.join(root, file)
                    try:
                        # Lire le contenu JSON
                        with open(file_path, 'r') as f:
                            raw = f.read()
                            data = json.loads(raw)
                            content_hash = data.get('contentHash')
                            if content_hash:
                                # Remplacer le fichier par son contenu binaire
                                extract_file_from_blob(content_hash, file_path)
                    except (json.JSONDecodeError, KeyError):
                        # Passer si le fichier n'est pas un JSON valide ou ne contient pas 'contentHash'
                        print(f"Fichier ignoré : {file_path}")
        
        # Stage des changements
        execute_git_command('git add .')

        # Récupérer les informations du commit actuel (auteur, date, message)
        commit_info = subprocess.check_output(f'git show --format="%an;%ae;%ad;%s" -s {commit}', shell=True, cwd=project_dir).decode('utf-8').strip()
        author_name, author_email, commit_date, commit_message = commit_info.split(';')

        # Créer le commit en conservant les informations originales
        commit_command = (
            f'GIT_COMMITTER_DATE="{commit_date}" '
            f'git commit --author="{author_name} <{author_email}>" '
            f'-m "{commit_message}"'
        )
        execute_git_command(commit_command)

# Fonction pour réinitialiser l'état du dépôt à HEAD après avoir tout reconstruit
def finalize_repo():
    # Retourner à la branche principale (par exemple, master) et pousser les changements
    execute_git_command('git checkout master')
    execute_git_command('git push --force')

if __name__ == "__main__":
    # Exécute la reconstruction de l'historique
    process_commits()
    finalize_repo()
