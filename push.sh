############################
# 1) Variables
############################
ARG CONDA_ENV_NAME=DWS-GPU
ARG PY_MAJOR=3.11
ARG ART_URL=https://repo.artifactory-dogen.group.echonet/artifactory
# dépôts internes pour wheels torch/mmcv (adapte les chemins si besoin)
ARG TORCH_WHEELS=${ART_URL}/wheels/pytorch/cu121/torch2.3/cp311
ARG MMCV_WHEELS=${ART_URL}/wheels/openmmlab/mmcv/cu121/torch2.3/cp311

############################
# 2) Conda côté *domino* et forcer Artifactory
############################
USER domino
RUN /opt/conda/bin/conda --version
RUN printf "%s\n" \
  "channels:" \
  "  - ${ART_URL}/api/conda/conda-forge" \
  "  - ${ART_URL}/api/conda/conda-main" \
  "channel_alias: ${ART_URL}/api/conda" \
  "default_channels: []" \
  "show_channel_urls: true" \
  "channel_priority: strict" \
  "ssl_verify: false" \
  > /home/domino/.condarc

############################
# 3) Préparer le YAML et créer le venv via conda
############################
# IMPORTANT : on enlève du YAML les libs GPU qu’on gère en pip,
# et on impose le bon nom d’environnement + version Python.
RUN sed -E -i 's/^name:.*/name: '"${CONDA_ENV_NAME}"'/' /tmp/environment.yml && \
    grep -q '^name: '"${CONDA_ENV_NAME}"'$' /tmp/environment.yml && \
    (grep -q '^dependencies:' /tmp/environment.yml || echo -e "\ndependencies:\n  - python=${PY_MAJOR}" >> /tmp/environment.yml) && \
    sed -E -i '/^[[:space:]]*-[[:space:]]*(pytorch|torchvision|torchaudio|torch|mmcv|mmengine|mmdet)([=><].*)?$/d' /tmp/environment.yml

# (ré)création propre du venv depuis environment.yml
RUN /opt/conda/bin/conda env remove -n "${CONDA_ENV_NAME}" || true
RUN /opt/conda/bin/conda env create -n "${CONDA_ENV_NAME}" -f /tmp/environment.yml

############################
# 4) Installer la pile GPU par pip (depuis Artifactory, sans internet)
############################
# Torch 2.3.1 cu121 + vision/audio alignés
RUN . /opt/conda/etc/profile.d/conda.sh && conda activate "${CONDA_ENV_NAME}" && \
    python -m pip install --no-cache-dir --no-index --find-links "${TORCH_WHEELS}" \
      "torch==2.3.1+cu121" "torchvision==0.18.1+cu121" "torchaudio==2.3.1+cu121"

# mmcv 2.1.0 depuis wheels internes, puis mmengine/mmdet en ligne interne
RUN . /opt/conda/etc/profile.d/conda.sh && conda activate "${CONDA_ENV_NAME}" && \
    python -m pip install --no-cache-dir --no-index --find-links "${MMCV_WHEELS}" "mmcv==2.1.0" && \
    python -m pip install --no-cache-dir "mmengine==0.10.4" "mmdet==3.3.0"

############################
# 5) (Option) Paquets métier depuis ton environment.txt interne
#    -> commenter ce bloc si tu n’en as pas besoin
############################
# ARG REQ_URL=${ART_URL}/raw/ifs/cardif/ton-projet/environments/environment.txt
# RUN . /opt/conda/etc/profile.d/conda.sh && conda activate "${CONDA_ENV_NAME}" && \
#     curl -fsSL "$REQ_URL" -o /tmp/requirements.txt && \
#     grep -vE '^(torch|torchvision|torchaudio|mmcv|mmengine|mmdet)($|==)' /tmp/requirements.txt > /tmp/req.clean.txt && \
#     python -m pip install --no-cache-dir -r /tmp/req.clean.txt

############################
# 6) Sanity check versions
############################
RUN . /opt/conda/etc/profile.d/conda.sh && conda activate "${CONDA_ENV_NAME}" && \
    python - <<'PY'
import torch, mmcv, mmengine, mmdet
print("Torch ", torch.__version__, " CUDA=", torch.version.cuda, " avail=", torch.cuda.is_available())
print("MMCV  ", mmcv.__version__)
print("MMEng ", mmengine.__version__)
print("MMDet ", mmdet.__version__)
assert torch.__version__.startswith("2.3."), torch.__version__
assert torch.version.cuda.startswith("12.1"), torch.version.cuda
assert mmcv.__version__.startswith("2.1."), mmcv.__version__
assert mmengine.__version__.startswith("0.10."), mmengine.__version__
assert mmdet.__version__.startswith("3.3."), mmdet.__version__
PY

############################
# 7) Nettoyage
############################
USER root
RUN /opt/conda/bin/conda clean -y --all
USER domino
