import os
import json
import zipfile
import git

# Chemin vers les fichiers ZIP
zip_dir = "/path/to/zip/files"
# Chemin vers les fichiers sources dans le dépôt
source_dir = "/path/to/source/files"

def extract_file_from_zip(content_hash, target_file):
    zip_file = os.path.join(zip_dir, f"{content_hash}.zip")
    if os.path.exists(zip_file):
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extract(target_file, source_dir)
        print(f"Extrait: {target_file} depuis {zip_file}")
        return True
    else:
        print(f"Fichier ZIP introuvable: {zip_file}")
        return False

def process_tree(tree, project_id, project, commit, project_blobs, writer):
    n = 0
    for blob in tree.blobs:
        raw = blob.data_stream.read().decode('utf-8')
        if len(raw) > 0:
            data = json.loads(raw)
            content_hash = data.get("contentHash")
            if content_hash:
                project_blobs[data['contentHash']] = None
                # Remplacer le contenu du fichier par celui extrait du ZIP
                file_path = os.path.join(source_dir, blob.path)
                if extract_file_from_zip(content_hash, blob.path):
                    record = {
                        "project_id": project_id,
                        "project_name": project['name'],
                        "owner_id": str(project['ownerId']),
                        "commit": str(commit),
                        "author": str(commit.author),
                        "authored_date": get_commit_date(commit),
                        "message": commit.message,
                        "path": blob.path,
                        "size": int(data['size']),
                        "hash": content_hash
                    }
                    writer.writerow(record)
                    n += 1
    return n

def process_project(project, writer):
    project_id = str(project['id'])
    git_path = "/path/to/project/repos/{}/{}".format(project_id[:4], project_id)
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
    for project in get_all('projects', {}, ['name', 'ownerId']):
        process_project(project, writer)
