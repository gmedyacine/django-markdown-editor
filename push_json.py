import os
import git
import csv

# Définir le chemin racine où se trouvent les sauvegardes des dépôts Git
source_root_path = "/home/migration-git/projectrepos/"
# Définir le chemin du fichier CSV contenant les informations des projets
csv_path = "/path/to/project_config.csv"
# URL racine pour GitLab où les dépôts seront poussés
GITLABOBS = "https://gitlab.example.com/obs_temp/"
# Token pour l'accès GitLab
GITLAB_TOKEN = "your_gitlab_access_token"

# Lire le fichier CSV pour déduire le chemin et nom du dépôt à partir de l'ID de projet
def read_project_info(csv_path):
    project_info = {}
    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            project_id = row["PROJECTSOURCEID"]
            project_name = row["NEWPROJECTNAME"]
            git_path = os.path.join(GITLABOBS, project_name + ".git")
            project_info[project_id] = {
                "project_name": project_name,
                "git_path": git_path
            }
    return project_info

# Trouver et pousser chaque dépôt vers l'URL cible
def push_repos_to_gitlab(source_root_path, project_info):
    for project_id, details in project_info.items():
        # Calculer le sous-dossier en fonction des quatre premiers caractères de l'ID
        subfolder = project_id[:4]
        repo_path = os.path.join(source_root_path, subfolder, project_id + ".git")

        # Vérifier si le dossier du dépôt existe
        if not os.path.isdir(repo_path):
            print(f"Dépôt introuvable pour {project_id} dans {repo_path}")
            continue

        # Initialiser le dépôt Git à partir de son dossier de sauvegarde
        try:
            repo = git.Repo(repo_path)
        except Exception as e:
            print(f"Erreur lors de l'initialisation du dépôt {project_id}: {e}")
            continue

        # Définir l'URL complète pour GitLab avec le token d'accès
        gitlab_url = details["git_path"].replace("https://", f"https://oauth2:{GITLAB_TOKEN}@")

        # Configurer le remote et pousser le dépôt vers GitLab
        try:
            if "origin" in repo.remotes:
                repo.delete_remote("origin")
            repo.create_remote("origin", gitlab_url)
            repo.git.push("--mirror", "origin")
            print(f"Dépôt {project_id} ({details['project_name']}) poussé avec succès vers {details['git_path']}")
        except Exception as e:
            print(f"Erreur lors du push du dépôt {project_id}: {e}")

# Exécuter le script principal
def main():
    project_info = read_project_info(csv_path)
    push_repos_to_gitlab(source_root_path, project_info)

if __name__ == "__main__":
    main()
