import os
import json
import git
import zipfile
from datetime import datetime

# Chemin du répertoire où sont stockés les blobs (ZIP ou autres)
blob_store_dir = "/path/to/blob/store"
# Chemin vers le répertoire contenant les fichiers source dans le dépôt
source_dir = "project_dir = "/tmp/test-synchro/projet-test"

def extract_file_from_blob(content_hash, target_file):
    """ Extrait le fichier binaire réel depuis les blobs (ZIP ou autres). """
    subdir = content_hash[:2]
    blob_path = os.path.join(blob_store_dir, subdir, content_hash)

    if os.path.exists(blob_path):
        # Si c'est un fichier ZIP, on extrait le contenu
        if blob_path.endswith(".zip"):
            with zipfile.ZipFile(blob_path, 'r') as zip_ref:
                zip_ref.extractall(source_dir)
            print(f"Extrait {target_file} depuis {blob_path}")
        else:
            # Si ce n'est pas un ZIP, on copie simplement le fichier
            with open(blob_path, 'rb') as src, open(os.path.join(source_dir, target_file), 'wb') as dest:
                dest.write(src.read())
            print(f"Copié {target_file} depuis {blob_path}")
        return True
    else:
        print(f"Blob introuvable: {blob_path}")
        return False

def replay_commit(repo, commit):
    """ Recrée le commit avec le contenu binaire réel et les métadonnées originales. """
    repo.git.checkout(commit)  # Se positionner sur le commit en question
    tree = commit.tree

    # Parcourir les fichiers dans ce commit
    for blob in tree.blobs:
        raw = blob.data_stream.read().decode('utf-8')

        # Vérifie si le fichier contient un contentHash (faux fichier JSON)
        if raw.strip():
            try:
                data = json.loads(raw)
                content_hash = data.get("contentHash")
                if content_hash:
                    # Remplacer le fichier par le contenu binaire réel
                    extract_file_from_blob(content_hash, blob.path)
                    repo.git.add(blob.path)
            except json.JSONDecodeError:
                print(f"Le fichier {blob.path} ne contient pas de JSON valide, on passe.")
                continue

    # Commiter avec les métadonnées d'origine
    author = commit.author
    authored_date = datetime.fromtimestamp(commit.authored_date)
    commit_message = commit.message

    repo.index.commit(
        commit_message,
        author=author,
        commit_date=authored_date.strftime("%Y-%m-%d %H:%M:%S"),
    )
    print(f"Commit recréé : {commit_message} à la date {authored_date}")

def main():
    # Charger le dépôt
    repo = git.Repo('/path/to/git/repo')

    # Parcourir l'historique des commits
    commits = list(repo.iter_commits('master'))

    for commit in reversed(commits):  # Refaire l'historique dans l'ordre chronologique
        replay_commit(repo, commit)

    # Pousser les modifications vers le dépôt distant
    repo.git.push('origin', 'master')

if __name__ == "__main__":
    main()
