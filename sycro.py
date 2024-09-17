import os
import json
import zipfile

# Chemin du répertoire où sont stockés les blobs (ZIP ou autres)
blob_store_dir = "/path/to/blob/store"
# Chemin vers le répertoire contenant les fichiers source dans le dépôt
source_dir = "/path/to/source/files"

def extract_file_from_blob(content_hash, target_file):
    """
    Extrait le fichier réel du blob en fonction du contentHash.
    Si c'est un ZIP, il extrait le fichier, sinon il copie simplement le fichier.
    """
    # Les deux premières lettres du contentHash définissent le sous-dossier
    subdir = content_hash[:2]
    # Chemin vers le fichier blob (ZIP ou autre)
    blob_path = os.path.join(blob_store_dir, subdir, content_hash)

    if os.path.exists(blob_path):
        # Si c'est un fichier ZIP, on l'extrait
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

def process_tree(tree, project_id, project, commit, project_blobs, writer):
    """
    Parcourt l'arborescence Git (les blobs) et remplace les fichiers avec le contenu réel des blobs.
    """
    n = 0
    for blob in tree.blobs:
        # Lire le fichier JSON à partir des blobs (similaire à ce que tu as dans les fichiers .py)
        raw = blob.data_stream.read().decode('utf-8')
        if len(raw) > 0:
            data = json.loads(raw)
            content_hash = data.get("contentHash")
            if content_hash:
                project_blobs[content_hash] = None
                # Extraire ou copier le fichier réel à partir du blob store
                file_path = os.path.join(source_dir, blob.path)
                if extract_file_from_blob(content_hash, blob.path):
                    # Log du processus, ajouter si nécessaire dans un fichier CSV
                    record = {
                        "project_id": project_id,
                        "project_name": project['name'],
                        "owner_id": str(project['ownerId']),
                        "commit": str(commit),
                        "author": str(commit.author),
                        "authored_date": commit.authored_date.strftime("%Y-%m-%d %H:%M:%S"),
                        "message": commit.message,
                        "path": blob.path,
                        "size": int(data['size']),
                        "hash": content_hash
                    }
                    writer.writerow(record)
                    n += 1
    return n

def process_project(project, writer):
    """
    Traite un projet Git, extrait les fichiers réels pour chaque commit, et les rétablit.
    """
    project_id = str(project['id'])
    git_path = f"/path/to/project/repos/{project_id[:4]}/{project_id}"
    repo = git.Repo(git_path)
    
    all_commits = set()
    project_blobs = {}
    
    for branch in repo.remote().refs:
        if 'HEAD' not in branch.name:
            repo.git.checkout(branch.name.split('/')[-1])
            all_commits.update(reversed(list(repo.iter_commits())))
    
    for commit in all_commits:
        process_tree(commit.tree, project_id, project, commit, project_blobs, writer)
    
    repo.__del__()

# Point d'entrée principal
if __name__ == "__main__":
    # Suppose que tu récupères la liste des projets
    for project in get_all('projects', {}, ['name', 'ownerId']):
        process_project(project, writer)
