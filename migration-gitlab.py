import os
import subprocess
import csv
import git

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
                "git_url": row["NewGitlabProject"],
                "token": row["GitlabToken"]  # Assurez-vous que la colonne du token est correcte
            })
    return project_info

# Fonction pour cloner le dépôt JSON depuis GitLab
def clone_json_repo(git_url, token, clone_dir):
    auth_git_url = git_url.replace("https://", f"https://{token}@")
    repo = git.Repo.clone_from(auth_git_url, clone_dir)
    return repo

# Fonction pour reconstituer les commits avec les vrais binaires
def reconstruct_commits_with_binaries(json_repo_dir, binaries_repo_dir, project_id):
    json_repo = git.Repo(json_repo_dir)
    os.makedirs(binaries_repo_dir, exist_ok=True)
    binaries_repo = git.Repo.init(binaries_repo_dir)

    for commit in json_repo.iter_commits('master'):  # Parcours de chaque commit
        json_repo.git.checkout(commit)  # Passage au commit actuel
        # Copier les binaires en remplaçant les faux fichiers JSON
        for root, _, files in os.walk(json_repo_dir):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                # Logique pour obtenir les binaires réels
                content_hash = extract_content_hash(file_path)
                binary_path = f"/var/opt/git/projectrepos/{content_hash[:2]}/{content_hash}.zip"  # Chemin du binaire
                if os.path.exists(binary_path):
                    shutil.copy(binary_path, os.path.join(binaries_repo_dir, file_name))
        
        binaries_repo.git.add(A=True)
        binaries_repo.index.commit(commit.message, author=commit.author, committer=commit.committer,
                                   author_date=commit.authored_date, commit_date=commit.committed_date)

    return binaries_repo

# Fonction principale
def main():
    project_info_list = read_project_info(csv_path)
    
    for project_info in project_info_list:
        print(f"Traitement du projet {project_info['project_id']}...")

        # Clone du dépôt JSON
        print("Clonage du dépôt JSON...")
        json_repo_dir = os.path.join(local_repo_dir, project_info["project_id"])
        repo = clone_json_repo(project_info["git_url"], project_info["token"], json_repo_dir)

        # Reconstruction du dépôt avec les binaires
        print("Reconstruction des commits avec les binaires...")
        binaries_repo = reconstruct_commits_with_binaries(json_repo_dir, binaries_repo_dir, project_info["project_id"])

        # Push vers la cible Git
        target_url = project_info["git_url"].replace("https://", f"https://{project_info['token']}@")
        binaries_repo.create_remote('target', target_url)
        binaries_repo.git.push('target', 'master', force=True)  # Push final

        print(f"Migration des binaires terminée pour le projet {project_info['project_id']}.")

if __name__ == "__main__":
    main()
