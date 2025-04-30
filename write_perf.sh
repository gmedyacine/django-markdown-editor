#!/usr/bin/env bash
# ↳ test-write.sh
set -euo pipefail
IFS=$'\n\t'

###############################################################################
# Paramètres
###############################################################################
TARGET_SIZE_GB=10          # volume à écrire par dataset (Go)
FILE_SIZE_MB=10            # taille d’un fichier (Mo)
LOG_FILE="write_speed.log" # journal de sortie

###############################################################################
# Détection automatique des datasets Domino
###############################################################################
MOUNT_POINTS=(/domino/datasets/*)

###############################################################################
# Calculs dérivés – ne rien modifier
###############################################################################
TARGET_SIZE_BYTES=$(( TARGET_SIZE_GB * 1024 * 1024 * 1024 ))
FILE_SIZE_BYTES=$(( FILE_SIZE_MB * 1024 * 1024 ))
FILES_PER_DATASET=$(( TARGET_SIZE_BYTES / FILE_SIZE_BYTES ))

###############################################################################
# En-tête du journal
###############################################################################
printf "=====  DOMINO DATA LAB WRITE TEST  =====\n"        | tee  "$LOG_FILE"
printf "Objectif : %d Go  (%d fichiers × %d Mo)\n" \
       "$TARGET_SIZE_GB" "$FILES_PER_DATASET" "$FILE_SIZE_MB"      | tee -a "$LOG_FILE"
printf "----------------------------------------\n\n"      | tee -a "$LOG_FILE"

###############################################################################
# Boucle principale
###############################################################################
for MNT in "${MOUNT_POINTS[@]}"; do
  [[ -d "$MNT" ]] || { echo "⚠️  $MNT n'existe pas – ignoré"; continue; }

  printf "→ %-40s " "$(basename "$MNT")" | tee -a "$LOG_FILE"

  bytes_written=0
  idx=0
  start=$(date +%s)

  while (( bytes_written < TARGET_SIZE_BYTES )); do
    # Écrit un seul fichier de 10 Mo et force le flush disque (conv=fsync)
    dd if=/dev/zero of="$MNT/file_${idx}.bin" \
       bs="${FILE_SIZE_MB}M" count=1 conv=fsync status=none
    (( bytes_written += FILE_SIZE_BYTES ))
    (( idx++ ))
  done

  end=$(date +%s)
  elapsed=$(( end - start ))
  (( elapsed == 0 )) && elapsed=1   # évite une division par zéro

  # Vitesse en MB/s
  speed=$(echo "scale=2; $bytes_written / $elapsed / 1024 / 1024" | bc)

  printf "%8.2f MB/s\n" "$speed" | tee -a "$LOG_FILE"
done

printf "\n✔️  Test terminé – détails dans %s\n" "$LOG_FILE"
