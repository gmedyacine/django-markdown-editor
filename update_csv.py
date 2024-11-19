import os
import shutil
from git import Repo, GitCommandError

# Variables à définir
repo_url = "https://gitlab-dogen.group.echonet/ifs/cardif/tribe_data_ai/domino_cardif_datalab_platform/migrationdata_dmzr.git"
repo_dir = "/path/to/local/repo"  # Remplacez par le chemin local où cloner le dépôt
branch_name = "dev"
csv_relative_path = "HPRD/migration.csv"
target_directory = "/path/to/target/directory"  # Dossier de destination pour le fichier CSV

# Clone ou mise à jour du dépôt
if not os.path.exists(repo_dir):
    print("Clonage du dépôt...")
    repo = Repo.clone_from(repo_url, repo_dir)
else:
    print("Mise à jour du dépôt existant...")
    repo = Repo(repo_dir)
    repo.git.pull()

# Changer de branche vers 'dev'
try:
    repo.git.checkout(branch_name)
    print(f"Changé vers la branche '{branch_name}'")
except GitCommandError as e:
    print(f"Erreur lors du changement de branche : {e}")
    exit(1)

# Chemin du fichier CSV dans le dépôt
csv_path = os.path.join(repo_dir, csv_relative_path)

# Vérifier si le fichier CSV existe
if os.path.exists(csv_path):
    # Déplacer le fichier CSV vers le dossier de destination
    print(f"Déplacement de {csv_relative_path} vers {target_directory}")
    shutil.move(csv_path, os.path.join(target_directory, os.path.basename(csv_relative_path)))
else:
    print(f"Fichier {csv_relative_path} introuvable dans le dépôt.")

print("Script terminé.")
