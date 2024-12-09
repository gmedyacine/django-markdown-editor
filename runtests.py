def extract_file_from_blob(content_hash, target_file):
    subdir = content_hash[:2]
    blob_path = os.path.join(blob_store_dir, subdir, content_hash)
    zip_path = blob_path + ".zip"

    if os.path.exists(zip_path):
        # Le fichier ZIP existe, on l'extrait
        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(os.path.dirname(target_file))
        return True
    elif os.path.exists(blob_path):
        # Le fichier ZIP n'existe pas mais le blob existe, on le copie
        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        shutil.copy(blob_path, target_file)
        return True
    else:
        print(f"Blob introuvable : {blob_path} ou {zip_path}")
        return False
