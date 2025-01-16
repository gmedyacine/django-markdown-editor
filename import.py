import tarfile

def extract_tar(archive_path, destination_path):
    """
    Décompresse un fichier .tar dans le dossier spécifié.
    
    :param archive_path: Chemin vers l'archive .tar
    :param destination_path: Chemin vers le dossier de destination
    """
    # Ouvre l'archive en lecture
    with tarfile.open(archive_path, 'r') as tar:
        # Extrait tous les fichiers dans le dossier de destination
        tar.extractall(path=destination_path)
    print(f"Fichiers extraits dans {destination_path}")

if __name__ == "__main__":
    # Exemples d'utilisation
    archive_path = "/chemin/vers/fichier.tar"
    destination_path = "/mnt/dataset/"
    
    extract_tar(archive_path, destination_path)
