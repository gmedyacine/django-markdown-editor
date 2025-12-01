SHELL ["/bin/bash","-lc"]
USER root
ARG CONDA_ENV_NAME=DWS-GPU

# (1) Créer/forcer l’env en Python 3.11 (si nécessaire)
RUN mamba env remove -n ${CONDA_ENV_NAME} -y || true \
 && mamba create -n ${CONDA_ENV_NAME} python=3.11.9 -y

# (2) Auth Artifactory pour ROOT
ARG DOCKERFILE_ARTIFACTORY_USERNAME
ARG DOCKERFILE_ARTIFACTORY_TOKEN
RUN printf "machine repo.artifactory-dogen.group.echonet\nlogin %s\npassword %s\n" \
    "$DOCKERFILE_ARTIFACTORY_USERNAME" "$DOCKERFILE_ARTIFACTORY_TOKEN" > /root/.netrc \
 && chmod 600 /root/.netrc

# (3) URLs cp311
ARG TORCH_WHEELS="https://repo.artifactory-dogen.group.echonet/artifactory/wheels/pytorch/cu121/"
ARG MMCV_WHEELS="https://repo.artifactory-dogen.group.echonet/artifactory/openmmlab/mmcv/cu121/torch2.3/"

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_DEFAULT_TIMEOUT=15

# (4) Install 100% offline via Artifactory (cp311)
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip install --no-cache-dir \
    --no-index --find-links ${TORCH_WHEELS} \
    torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 \
 && /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip install --no-cache-dir \
    mmengine==0.10.4 mmdet==3.3.0 \
 && /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip install --no-cache-dir --force-reinstall \
    --no-index --find-links ${MMCV_WHEELS} \
    mmcv==2.1.0

# (5) Sanity
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python - <<'PY'
import sys, torch, mmcv
print(sys.version)
print("torch", torch.__version__, "cuda", torch.version.cuda, "avail", torch.cuda.is_available())
print("mmcv", mmcv.__version__)
PY

USER domino
