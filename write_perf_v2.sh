#!/usr/bin/env bash
# ↳ test-write-iops.sh
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
# Calculs dérivés
###############################################################################
TARGET_SIZE_BYTES=$(( TARGET_SIZE_GB * 1024 * 1024 * 1024 ))
FILE_SIZE_BYTES=$(( FILE_SIZE_MB * 1024 * 1024 ))
FILES_PER_DATASET=$(( TARGET_SIZE_BYTES / FILE_SIZE_BYTES ))

###############################################################################
# En-tête du journal
###############################################################################
{
  printf "=====  DOMINO DATA LAB WRITE TEST  =====\n"
  printf "Objectif : %d Go  (%d fichiers × %d Mo)\n" \
         "$TARGET_SIZE_GB" "$FILES_PER_DATASET" "$FILE_SIZE_MB"
  printf "-----------------------------------------------------------------------\n"
  printf "%-30s %10s %10s %12s %12s %12s\n" \
         "DATASET" "MB/s" "IOPS" "Lat_avg(ms)" "Lat_min(ms)" "Lat_max(ms)"
} | tee  "$LOG_FILE"

###############################################################################
# Boucle principale
###############################################################################
for MNT in "${MOUNT_POINTS[@]}"; do
  [[ -d "$MNT" ]] || { echo "⚠️  $MNT n'existe pas – ignoré" | tee -a "$LOG_FILE"; continue; }

  bytes_written=0
  idx=0
  lat_total_ns=0
  lat_min_ns=999999999999
  lat_max_ns=0

  start_ns=$(date +%s%N)   # début dataset

  while (( bytes_written < TARGET_SIZE_BYTES )); do
    op_start_ns=$(date +%s%N)

    # écriture d’un fichier de 10 Mo et flush direct disque
    dd if=/dev/zero of="$MNT/file_${idx}.bin" \
       bs="${FILE_SIZE_MB}M" count=1 conv=fsync status=none

    op_end_ns=$(date +%s%N)
    op_lat_ns=$(( op_end_ns - op_start_ns ))

    (( lat_total_ns += op_lat_ns ))
    (( op_lat_ns < lat_min_ns )) && lat_min_ns=$op_lat_ns
    (( op_lat_ns > lat_max_ns )) && lat_max_ns=$op_lat_ns

    (( bytes_written += FILE_SIZE_BYTES ))
    (( ++idx ))
  done

  end_ns=$(date +%s%N)
  elapsed_ns=$(( end_ns - start_ns ))
  elapsed_s=$(echo "scale=6; $elapsed_ns/1000000000" | bc)   # secondes décimal
  (( elapsed_ns == 0 )) && elapsed_ns=1                      # anti /0 improbable

  # --- métriques ---
  mb_per_s=$(echo "scale=2; $bytes_written / $elapsed_s / 1024 / 1024" | bc)
  iops=$(echo "scale=2; $idx / $elapsed_s" | bc)
  lat_avg_ms=$(echo "scale=3; $lat_total_ns / $idx / 1000000" | bc)
  lat_min_ms=$(echo "scale=3; $lat_min_ns / 1000000" | bc)
  lat_max_ms=$(echo "scale=3; $lat_max_ns / 1000000" | bc)

  # --- affichage / log ---
  printf "%-30s %10.2f %10.2f %12.3f %12.3f %12.3f\n" \
         "$(basename -- "$MNT")" \
         "$mb_per_s" "$iops" "$lat_avg_ms" "$lat_min_ms" "$lat_max_ms" \
         | tee -a "$LOG_FILE"
done

echo -e "\n✔️  Test terminé – détails complets dans ${LOG_FILE}" | tee -a "$LOG_FILE"
