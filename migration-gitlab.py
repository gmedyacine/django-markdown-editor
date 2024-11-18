import os
import subprocess
import csv
import git
import shutil

# Variables globales
csv_path = "/chemin/vers/votre_fichier.csv"
local_repo_dir = "/tmp/fake_git_repo_clone"
binaries_repo_dir = "/tmp/real_binaries_repo"
pod_name = "git-0"
namespace = "domino-platform"

# Fonction pour lire le CSV et récupérer les informations nécessaires
def read_project_info(csv_path):
    project_info = []
    with open(csv_path, mode="r") as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            project_info.append({
                "project_id": row["ProjectSourceID"],
                "project_name": row["ProjectSourcePath"],
                "git_url_json": row["NewGitlabProject"],  # URL pour le dépôt de faux fichiers JSON
                "git_url_binaries": row["ProjectNewName"],  # URL pour le dépôt de binaires cible
                "token": row["GitlabToken"]  # Assurez-vous que la colonne du token est correcte
            })
    return project_info

# Fonction pour cloner le dépôt JSON depuis GitLab
def clone_json_repo(git_url, token, clone_dir):
    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir)
    auth_git_url = git_url.replace("https://", f"https://{token}@")
    repo = git.Repo.clone_from(auth_git_url, clone_dir)
    return repo
# Fonction pour extraire le content hash d'un fichier JSON
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

# Fonction pour recréer les commits avec les binaires dans le nouveau dépôt
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


# Fonction pour effectuer le push vers le dépôt cible
def push_to_target_repo(local_repo_dir, url_git, token):
    auth_url_git = url_git.replace("https://", f"https://{token}@")
    repo = git.Repo(local_repo_dir)
    repo.create_remote('target', auth_url_git)
    repo.git.push('--mirror', 'target')  # Push avec mirroring complet

# Fonction principale
def main():
    project_info_list = read_project_info(csv_path)
    
    for project_info in project_info_list:
        print(f"Traitement du projet {project_info['project_id']}...")

        # Clone du dépôt JSON
        print("Clonage du dépôt JSON...")
        json_repo_dir = os.path.join(local_repo_dir, project_info["project_id"])
        clone_json_repo(project_info["git_url_json"], project_info["token"], json_repo_dir)

        # Reconstruction du dépôt avec les binaires
        print("Reconstruction des commits avec les binaires...")
        recreate_commit_with_binaries(json_repo_dir, binaries_repo_dir)

        # Push vers la cible Git des binaires
        print("Push du dépôt binaire vers la cible...")
        push_to_target_repo(binaries_repo_dir, project_info["git_url_binaries"], project_info["token"])

        # Nettoyage pour la prochaine itération
        shutil.rmtree(json_repo_dir)
        shutil.rmtree(binaries_repo_dir)
        os.makedirs(binaries_repo_dir, exist_ok=True)

        print(f"Migration des binaires terminée pour le projet {project_info['project_id']}.")

if __name__ == "__main__":
    main()
