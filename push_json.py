import os
import subprocess
import csv
import git

# Paramètres globaux
pod_name = "git-0"
namespace = "default"  # Assurez-vous de remplacer par le bon namespace
local_repo_dir = "/tmp/git_repo_clone"

# Fonction pour lire les informations de projet depuis un fichier CSV
def read_project_info(csv_path):
    project_info = []
    with open(csv_path, mode="r") as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            project_info.append({
                "project_id": row["ProjectSourceID"],
                "repo_path": row["ProjectSourcePath"],
                "url_git": row["NewGitLabGroup"],
                "token_git": row["NewProjectContributorAccess"]
            })
    return project_info

# Fonction pour exécuter une commande dans le pod
def exec_in_pod(pod, namespace, command):
    cmd = ["kubectl", "exec", pod, "-n", namespace, "--"] + command
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Erreur lors de l'exécution de la commande {command} dans le pod {pod}")
        print(result.stderr)
    return result.stdout

# Fonction pour cloner le dépôt depuis le pod
def clone_repo_from_pod(pod, namespace, repo_path):
    os.makedirs(local_repo_dir, exist_ok=True)
    tar_cmd = ["tar", "-czf", "-", "-C", repo_path, "."]
    untar_cmd = ["tar", "-xzf", "-", "-C", local_repo_dir]
    
    # Exécuter la commande de tar dans le pod et récupérer la sortie en tant que stream
    tar_process = subprocess.Popen(
        ["kubectl", "exec", pod, "-n", namespace, "--"] + tar_cmd,
        stdout=subprocess.PIPE
    )
    untar_process = subprocess.Popen(untar_cmd, stdin=tar_process.stdout)
    
    # Assurez-vous que les deux processus terminent correctement
    tar_process.stdout.close()  # Fermer le stream d'entrée du processus untar
    tar_process.wait()
    untar_process.wait()

# Fonction pour effectuer le push vers le dépôt cible
def push_to_target_repo(local_repo_dir, url_git, token_git):
    # Ajouter les informations de token dans l'URL du remote
    auth_url_git = url_git.replace("https://", f"https://{token_git}@")
    repo = git.Repo(local_repo_dir)
    repo.create_remote('target', auth_url_git)
    repo.git.push('--mirror', 'target')

# Fonction principale
def main():
    csv_path = "/path/to/template.csv"  # Chemin vers votre fichier CSV
    project_info = read_project_info(csv_path)
    
    for project in project_info:
        print(f"Traitement du projet {project['project_id']}...")
        
        # Cloner le repo depuis le pod
        print("Clonage du dépôt depuis le pod...")
        clone_repo_from_pod(pod_name, namespace, os.path.join("/var/opt/git/projectrepos", project["repo_path"]))
        
        # Effectuer le push vers le dépôt cible
        print("Push vers le dépôt cible...")
        push_to_target_repo(local_repo_dir, project["url_git"], project["token_git"])

        # Nettoyage du dossier temporaire pour la prochaine itération
        for root, dirs, files in os.walk(local_repo_dir, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(local_repo_dir)

    print("Migration terminée.")

if __name__ == "__main__":
    main()
