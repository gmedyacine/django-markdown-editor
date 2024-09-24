import os
import shutil
import zipfile
import json
import git
from datetime import datetime

# Chemin du répertoire où sont stockés les blobs (ZIP ou autres)
blob_store_dir = "/path/to/blob/store"
# Créer un répertoire temporaire vide pour les fichiers extraits
source_dir = "/path/to/empty/folder"  # Ce dossier contiendra les vrais binaires

# Nouveau dossier où recréer le dépôt avec les bons binaires
new_repo_path = "/path/to/new/repo"

# S'assurer que le répertoire temporaire pour les binaires est vide
if os.path.exists(source_dir):
    shutil.rmtree(source_dir)
os.makedirs(source_dir)

def extract_file_from_blob(content_hash, target_file):
    """ Extrait le fichier binaire réel depuis les blobs (ZIP ou autres) dans un répertoire temporaire. """
    subdir = content_hash[:2]  # Première partie du contentHash pour organiser les blobs
    blob_path = os.path.join(blob_store_dir, subdir, content_hash)

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

def recreate_commit_with_binaries(new_repo, commit, repo):
    """ Recrée le commit avec les fichiers binaires dans le nouveau dépôt, avec les métadonnées du commit d'origine. """
    repo.git.checkout(commit)  # Se positionner sur le commit en question
    tree = commit.tree

    # Parcourir les fichiers dans ce commit et les remplacer par les bons binaires
    for blob in tree.traverse():
        if blob.type == 'blob':
            raw = blob.data_stream.read().decode('utf-8')

            # Vérifie si le fichier contient un contentHash (faux fichier JSON)
            if raw.strip():
                try:
                    data = json.loads(raw)
                    content_hash = data.get("contentHash")
                    if content_hash:
                        # Extraire le fichier binaire réel dans source_dir
                        if extract_file_from_blob(content_hash, blob.path):
                            # Copier le fichier binaire dans le nouveau dépôt
                            source_file = os.path.join(source_dir, blob.path)
                            target_file = os.path.join(new_repo.working_tree_dir, blob.path)

                            # Vérifier si le fichier source existe avant de le copier
                            if os.path.exists(source_file):
                                os.makedirs(os.path.dirname(target_file), exist_ok=True)
                                shutil.copy(source_file, target_file)
                                new_repo.git.add(target_file)
                            else:
                                print(f"Erreur : Le fichier {source_file} est introuvable.")
                                continue
                except json.JSONDecodeError:
                    print(f"Le fichier {blob.path} ne contient pas de JSON valide, on passe.")
                    continue

    # Commiter dans le nouveau dépôt avec les métadonnées d'origine
    author = commit.author
    authored_date = datetime.fromtimestamp(commit.authored_date)
    commit_message = commit.message

    new_repo.index.commit(
        commit_message,
        author=author,
        commit_date=authored_date.strftime("%Y-%m-%d %H:%M:%S"),
    )
    print(f"Commit recréé dans le nouveau dépôt : {commit_message} à la date {authored_date}")

def main():
    # Charger le dépôt contenant les faux fichiers JSON (ancien dépôt)
    repo_path = "/path/to/git/repo"  # Le chemin vers le dépôt Git contenant les faux fichiers
    repo = git.Repo(repo_path)

    # Créer un nouveau dépôt dans un nouveau dossier
    if os.path.exists(new_repo_path):
        shutil.rmtree(new_repo_path)
    os.makedirs(new_repo_path)
    new_repo = git.Repo.init(new_repo_path)

    # Parcourir l'historique des commits dans la branche spécifiée (ex : master-b)
    commits = list(repo.iter_commits('master-b'))

    # Recréer chaque commit dans le nouveau dépôt
    for commit in reversed(commits):  # Rejouer dans l'ordre chronologique
        recreate_commit_with_binaries(new_repo, commit, repo)

    # Pousser les modifications vers un dépôt distant, si nécessaire
    # new_repo.git.push('origin', 'new-branch', force=True)  # Forcer le push sur une nouvelle branche

if __name__ == "__main__":
    main()
