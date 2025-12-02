# ===== GPU stack via Artifactory (no Internet) =====
USER domino

# Variables
ARG CONDA_ENV_NAME=DWS-GPU
ARG PY_MAJOR=3.11
ARG ART_URL=https://repo.artifactory-dogen.group.echonet/artifactory
ARG DOCKERFILE_ARTIFACTORY_USERNAME
ARG DOCKERFILE_ARTIFACTORY_TOKEN

ENV ENV_PATH=/opt/conda/envs/${CONDA_ENV_NAME} \
    CONDA_ENVS_PATH=/opt/conda/envs \
    CONDA_PKGS_DIRS=/home/domino/.conda/pkgs \
    CONDA_ALWAYS_YES=true \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=70

# Auth pip (si wheels privés)
RUN printf "machine repo.artifactory-dogen.group.echonet login %s password %s\n" \
    "${DOCKERFILE_ARTIFACTORY_USERNAME}" "${DOCKERFILE_ARTIFACTORY_TOKEN}" > ~/.netrc || true && \
    chmod 600 ~/.netrc || true && \
    mkdir -p /home/domino/.conda/pkgs

# Purge des champs problématiques et des restes torch* dans le YAML
RUN sed -i -E '/^[[:space:]]*name:/d; \
               /^[[:space:]]*prefix:/d; \
               /^[[:space:]]*pytorch([:=]|$)/d; \
               /^[[:space:]]*torchvision([:=]|$)/d; \
               /^[[:space:]]*torchaudio([:=]|$)/d' /tmp/environment.yml

# Forcer les channels conda -> Artifactory uniquement
RUN /opt/conda/bin/conda config --set ssl_verify false && \
    (/opt/conda/bin/conda config --remove-key default_channels || true) && \
    (/opt/conda/bin/conda config --remove-key channels || true) && \
    /opt/conda/bin/conda config --add channels "${ART_URL}/api/conda/conda-forge" && \
    /opt/conda/bin/conda config --add channels "${ART_URL}/api/conda/conda-main" && \
    /opt/conda/bin/conda config --set show_channel_urls true

# (Re)création propre par PREFIX (pas de -n)
RUN /opt/conda/bin/conda env remove --prefix "${ENV_PATH}" || true && \
    /opt/conda/bin/conda env create --prefix "${ENV_PATH}" \
        --file /tmp/environment.yml \
        --override-channels \
        -c "${ART_URL}/api/conda/conda-forge" \
        -c "${ART_URL}/api/conda/conda-main" \
        --quiet && \
    /opt/conda/bin/conda clean -y --all

# Wheels internes
ARG TORCH_WHEELS=${ART_URL}/wheels/pytorch/cu121/torch2.3/cp311/
ARG MMCV_WHEELS=${ART_URL}/wheels/openmlab/mmcv/cu121/torch2.3/cp311/

# 1) Torch 2.3.1 cu121 (offline)
RUN "${ENV_PATH}/bin/pip" install --no-cache-dir --no-index \
    --find-links="${TORCH_WHEELS}" \
    torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1

# 2) mmcv/mmengine/mmdet (offline) dans cet ordre
RUN "${ENV_PATH}/bin/pip" install --no-cache-dir --no-index \
    --find-links="${MMCV_WHEELS}" \
    mmcv==2.1.0 mmengine==0.10.4 mmdet==3.3.0

# 3) Sanity check strict (fail le build si mismatch)
RUN "${ENV_PATH}/bin/python" - <<'PY'
import torch, mmcv, mmengine, mmdet
print("Torch", torch.__version__, "CUDA", torch.version.cuda, "avail", torch.cuda.is_available())
print("mmcv", mmcv.__version__, "mmengine", mmengine.__version__, "mmdet", mmdet.__version__)
assert torch.__version__.startswith("2.3.1")
assert (torch.version.cuda or "").startswith("12.1")
assert mmcv.__version__.startswith("2.1.")
assert mmengine.__version__ == "0.10.4"
assert mmdet.__version__.startswith("3.3.")
PY
# ===== end =====
