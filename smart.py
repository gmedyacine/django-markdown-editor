import os
import shutil
import zipfile
import json
import git
from datetime import datetime

# Chemin du répertoire où sont stockés les blobs (ZIP ou autres)
blob_store_dir = "/path/to/blob/store"
# Créer un répertoire temporaire vide pour les fichiers extraits
source_dir = "/path/to/empty/folder"

# S'assurer que le répertoire est vide avant de commencer
if os.path.exists(source_dir):
    shutil.rmtree(source_dir)  # Supprime le répertoire s'il existe déjà
os.makedirs(source_dir)  # Crée un nouveau répertoire vide

def extract_file_from_blob(content_hash, target_file):
    """ Extrait le fichier binaire réel depuis les blobs (ZIP ou autres) dans un répertoire temporaire. """
    subdir = content_hash[:2]  # Première partie du contentHash pour organiser les blobs
    blob_path = os.path.join(blob_store_dir, subdir, content_hash)

    # Affiche le chemin du blob pour vérifier s'il existe bien
    print(f"Chemin du blob : {blob_path}")

    if os.path.exists(blob_path):
        # Vérifie si c'est un fichier ZIP ou un fichier normal
        if blob_path.endswith(".zip"):
            with zipfile.ZipFile(blob_path, 'r') as zip_ref:
                zip_ref.extractall(source_dir)
            print(f"Extrait {target_file} depuis {blob_path}")
        else:
            # Crée les répertoires cibles s'ils n'existent pas
            full_target_path = os.path.join(source_dir, target_file)
            os.makedirs(os.path.dirname(full_target_path), exist_ok=True)  # S'assure que les répertoires existent

            # Copier le fichier directement
            with open(blob_path, 'rb') as src, open(full_target_path, 'wb') as dest:
                dest.write(src.read())
            print(f"Copié {target_file} depuis {blob_path} vers {full_target_path}")
        return True
    else:
        print(f"Blob introuvable : {blob_path}")
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
                    # Extraire le fichier binaire réel dans source_dir
                    if extract_file_from_blob(content_hash, blob.path):
                        # Chemin du fichier source extrait
                        source_file = os.path.join(source_dir, blob.path)

                        # Vérifier si le fichier source existe avant de le copier
                        if os.path.exists(source_file):
                            # Remplacer le faux fichier JSON par le fichier réel dans repo_path
                            print(f"Remplacement de {blob.path} par {source_file}")
                            shutil.copy(source_file, os.path.join(repo.working_tree_dir, blob.path))
                            repo.git.add(blob.path)
                        else:
                            print(f"Erreur : Le fichier {source_file} est introuvable.")
                            continue
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
    repo_path = "/path/to/git/repo"  # Le chemin vers le dépôt Git principal (avec les faux fichiers JSON)
    repo = git.Repo(repo_path)

    # Parcourir l'historique des commits
    commits = list(repo.iter_commits('master-b'))  # Remplace 'master-b' par ta branche

    for commit in reversed(commits):  # Refaire l'historique dans l'ordre chronologique
        replay_commit(repo, commit)

    # Pousser les modifications vers le dépôt distant
    repo.git.push('origin', 'master-b')  # Pousser sur la branche correcte

if __name__ == "__main__":
    main()
