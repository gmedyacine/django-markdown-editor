# ====== GPU stack (Artifactory only) ======
# Prérequis: tu as déjà fait les sed pour retirer pytorch/torchvision/torchaudio du YAML.

USER domino
ARG CONDA_ENV_NAME=DWS-GPU
ARG PY_MAJOR=3.11
ARG ART_URL=https://repo.artifactory-dogen.group.echonet/artifactory
ARG DOCKERFILE_ARTIFACTORY_USERNAME
ARG DOCKERFILE_ARTIFACTORY_TOKEN

# Auth pip (si Artifactory demande un login pour /wheels)
RUN printf "machine repo.artifactory-dogen.group.echonet login %s password %s\n" \
    "${DOCKERFILE_ARTIFACTORY_USERNAME}" "${DOCKERFILE_ARTIFACTORY_TOKEN}" > ~/.netrc && \
    chmod 600 ~/.netrc

# Forcer conda à n’utiliser QUE Artifactory
RUN /opt/conda/bin/conda config --set ssl_verify false && \
    (/opt/conda/bin/conda config --remove-key default_channels || true) && \
    (/opt/conda/bin/conda config --remove-key channels || true) && \
    /opt/conda/bin/conda config --add channels "${ART_URL}/api/conda/conda-forge" && \
    /opt/conda/bin/conda config --add channels "${ART_URL}/api/conda/conda-main" && \
    /opt/conda/bin/conda config --set show_channel_urls true

# (Re)création propre de l’environnement depuis le YAML (sans torch*)
RUN /opt/conda/bin/conda env remove -n "${CONDA_ENV_NAME}" || true && \
    /opt/conda/bin/conda env create -n "${CONDA_ENV_NAME}" \
      -f /tmp/environment.yml \
      --override-channels \
      -c "${ART_URL}/api/conda/conda-forge" \
      -c "${ART_URL}/api/conda/conda-main" \
      --quiet && \
    /opt/conda/bin/conda clean -y --all

# Chemins wheels internes (adapte si besoin)
ARG TORCH_WHEELS="${ART_URL}/wheels/pytorch/cu121/torch2.3/cp311/"
ARG MMCV_WHEELS="${ART_URL}/wheels/openmlab/mmcv/cu121/torch2.3/cp311/"

# 1) Torch/cu121 offline
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/pip install --no-cache-dir --no-index \
    --find-links="${TORCH_WHEELS}" \
    torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1

# 2) mm* offline (versions validées)
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/pip install --no-cache-dir --no-index \
    --find-links="${MMCV_WHEELS}" \
    mmengine==0.10.4 mmdet==3.3.0 mmcv==2.1.0

# 3) Sanity check strict (fail le build si mismatch)
RUN /opt/conda/bin/conda run -n "${CONDA_ENV_NAME}" python - <<'PY'
import torch, mmcv, mmengine, mmdet, sys
print("Torch", torch.__version__, "CUDA", torch.version.cuda, "avail", torch.cuda.is_available())
print("mmcv", mmcv.__version__, "mmengine", mmengine.__version__, "mmdet", mmdet.__version__)
assert torch.__version__.startswith("2.3.1"), f"Torch != 2.3.1 ({torch.__version__})"
assert (torch.version.cuda or "").startswith("12.1"), f"CUDA != 12.1 ({torch.version.cuda})"
assert mmcv.__version__.startswith("2.1"), f"mmcv != 2.1.x ({mmcv.__version__})"
assert mmengine.__version__.startswith("0.10.4"), f"mmengine != 0.10.4 ({mmengine.__version__})"
assert mmdet.__version__.startswith("3.3"), f"mmdet != 3.3.x ({mmdet.__version__})"
PY

# (Optionnel) petit nettoyage côté root après install
USER root
RUN rm -rf /var/lib/apt/lists/* /var/cache/apt/* /etc/apt/auth.conf.d/artifactory.conf \
           /home/domino/.config/pip/pip.conf /home/domino/.condarc || true
USER domino
# ====== fin du bloc ======
