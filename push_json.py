import csv
import subprocess
import os

# Fonction pour lire les informations de projet depuis le fichier CSV
def read_project_info(csv_path):
    project_info = []
    with open(csv_path, mode="r") as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            project_info.append({
                "project_id": row["ProjectSourceID"],
                "gitlab_url": row["NewGitlabGroup"],
                "project_path": row["ProjectSourcePath"]
            })
    return project_info

# Fonction pour exécuter une commande dans le pod et retourner la sortie
def exec_in_pod(command):
    kubectl_cmd = ["kubectl", "exec", "-i", "git-0", "--"] + command
    result = subprocess.run(kubectl_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Erreur lors de l'exécution de la commande : {result.stderr}")
        raise RuntimeError(result.stderr)
    return result.stdout.strip()

# Fonction principale pour pousser les projets
def push_projects_from_pod(project_info_list):
    for project_info in project_info_list:
        project_id = project_info["project_id"]
        gitlab_url = project_info["gitlab_url"]
        project_path = f"/var/opt/git/projectrepos/{project_id[:4]}/{project_id}.git"
        
        # Configurer le remote GitLab dans le pod
        print(f"Configuration du remote pour {project_path}")
        exec_in_pod(["git", "-C", project_path, "remote", "set-url", "origin", gitlab_url])
        
        # Push vers GitLab
        print(f"Push des blobs et refs pour {project_path} vers {gitlab_url}")
        try:
            exec_in_pod(["git", "-C", project_path, "push", "--mirror", "origin"])
            print(f"Push réussi pour {project_path}")
        except RuntimeError as e:
            print(f"Erreur lors du push pour {project_path}: {e}")

# Chemin du fichier CSV
csv_path = "/path/to/your/csvfile.csv"

# Lecture des informations du fichier CSV
project_info_list = read_project_info(csv_path)

# Exécution du push pour chaque projet
push_projects_from_pod(project_info_list)
