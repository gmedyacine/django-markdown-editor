# --- retire les paquets CPU qui sabotent la pile GPU ---
RUN sed -i -E '/^[[:space:]]*-[[:space:]]*pytorch=/d; \
               /^[[:space:]]*-[[:space:]]*torchvision=/d; \
               /^[[:space:]]*-[[:space:]]*torchaudio=/d' /tmp/environment.yml
SHELL ["/bin/bash","-lc"]
USER root
ARG CONDA_ENV_NAME=DWS-GPU

# Auth Artifactory pour root (sinon 403/404 aléatoires)
ARG DOCKERFILE_ARTIFACTORY_USERNAME
ARG DOCKERFILE_ARTIFACTORY_TOKEN
RUN printf "machine repo.artifactory-dogen.group.echonet\nlogin %s\npassword %s\n" \
    "$DOCKERFILE_ARTIFACTORY_USERNAME" "$DOCKERFILE_ARTIFACTORY_TOKEN" > /root/.netrc \
 && chmod 600 /root/.netrc
# index pypi interne par défaut
RUN printf "[global]\nindex-url = https://repo.artifactory-dogen.group.echonet/artifactory/api/pypi/pypi/simple\ntrusted-host = repo.artifactory-dogen.group.echonet\n" > /etc/pip.conf

# Purge sûre (idempotent)
RUN mamba remove -n ${CONDA_ENV_NAME} -y 'pytorch*' 'torchvision*' 'torchaudio*' 'pytorch-cuda*' || true
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip uninstall -y torch torchvision torchaudio mmcv mmcv-full mmengine mmdet || true

# Dossiers de wheels internes (adapter cp311 -> cp310 si votre env est en Py3.10)
ARG TORCH_WHEELS=https://repo.artifactory-dogen.group.echonet/artifactory/wheels/pytorch/cu121/cp311/
ARG MMCV_WHEELS=https://repo.artifactory-dogen.group.echonet/artifactory/openmmlab/mmcv/cu121/torch2.3/cp311/
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_DEFAULT_TIMEOUT=20

# 1) Torch cu121 offline
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip install --no-cache-dir --no-index \
    --find-links ${TORCH_WHEELS} \
    torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1

# 2) mmengine + mmdet via l’index interne (ou en wheels si vous les avez mirrorrés)
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip install --no-cache-dir \
    mmengine==0.10.4 mmdet==3.3.0

# 3) mmcv 2.1.0 offline (wheel interne)
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip install --no-cache-dir --no-index \
    --find-links ${MMCV_WHEELS} --force-reinstall \
    mmcv==2.1.0

# 4) Sanity & garde-fous
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python - <<'PY'
import sys, torch, mmcv, mmengine, mmdet
print("PY", sys.version.split()[0], "| torch", torch.__version__, "cuda", torch.version.cuda, "avail", torch.cuda.is_available())
print("mmcv", mmcv.__version__, "| mmengine", mmengine.__version__, "| mmdet", mmdet.__version__)
assert torch.__version__.startswith("2.3."), "Torch != 2.3.x"
assert mmcv.__version__.startswith("2.1."), "MMCV != 2.1.x"
assert mmdet.__version__.startswith("3.3."), "MMDet != 3.3.x"
PY

USER domino





------
ARG CONDA_ENV_NAME=DWS-GPU

# 0) Auth Artifactory (utilisé par pip) — à faire en root
USER root
ARG DOCKERFILE_ARTIFACTORY_USERNAME
ARG DOCKERFILE_ARTIFACTORY_TOKEN
RUN printf "machine repo.artifactory-dogen.group.echonet login %s password %s\n" \
      "$DOCKERFILE_ARTIFACTORY_USERNAME" "$DOCKERFILE_ARTIFACTORY_TOKEN" > /root/.netrc \
 && chmod 600 /root/.netrc \
 && printf "[global]\nindex-url = https://repo.artifactory-dogen.group.echonet/artifactory/api/pypi/pypi/simple\ntrusted-host = repo.artifactory-dogen.group.echonet\n" > /etc/pip.conf

# 1) Purge idempotent (ignore les erreurs si non installés)
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip uninstall -y \
      torch torchvision torchaudio pytorch-cuda torchtext \
      mmcv mmcv-full mmengine mmdet || true

# 2) Emplacements des wheels internes
ARG CUDA_TAG=cu121
ARG TORCH_VER=2.3.1
ARG PYTAG=cp311                 # cp310 si Python 3.10
ARG TORCH_WHEELS=https://repo.artifactory-dogen.group.echonet/artifactory/wheels/pytorch/${CUDA_TAG}/torch${TORCH_VER%.*}/${PYTAG}
ARG MMCV_WHEELS=https://repo.artifactory-dogen.group.echonet/artifactory/openmmlab/mmcv/${CUDA_TAG}/torch${TORCH_VER%.*}/${PYTAG}
ENV PIP_DEFAULT_TIMEOUT=120

# 3) Torch stack (offline depuis Artifactory wheels)
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip install --no-cache-dir --no-index \
      --find-links ${TORCH_WHEELS} \
      torch==${TORCH_VER} torchvision==0.18.1 torchaudio==2.3.1

# 4) mmengine + mmdet (depuis index mirrorré)
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip install --no-cache-dir \
      mmengine==0.10.4 mmdet==3.3.0

# 5) mmcv 2.1.0 (wheel interne)
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip install --no-cache-dir --no-index \
      --find-links ${MMCV_WHEELS} \
      mmcv==2.1.0

# 6) Sanity check (échoue le build si mismatch)
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python - <<'PY'
import torch, mmcv, mmengine, mmdet
print("Torch:", torch.__version__, "CUDA:", torch.version.cuda, "avail:", torch.cuda.is_available())
print("mmcv:", mmcv.__version__, "mmengine:", mmengine.__version__, "mmdet:", mmdet.__version__)
assert torch.__version__.startswith("2.3."), torch.__version__
assert (torch.version.cuda or "").startswith("12.1"), torch.version.cuda
assert mmcv.__version__.startswith("2.1."), mmcv.__version__
assert mmengine.__version__.startswith("0.10."), mmengine.__version__
assert mmdet.__version__.startswith("3.3."), mmdet.__version__
PY

# (ne pas nettoyer pip/conda ici ; le FOOTER s'en occupe)
#####################################################################










USER domino
ARG CONDA_ENV_NAME=DWS-GPU
ARG PY_MAJOR=3.11

# 0) créer l'env s'il n'existe pas (évite "No prefix")
RUN test -d "/opt/conda/envs/${CONDA_ENV_NAME}" \
 || mamba create -y -n "${CONDA_ENV_NAME}" "python=${PY_MAJOR}"

# 1) aligner le name: du YAML (ou le supprimer)
#    Option A: forcer le name à CONDA_ENV_NAME
RUN sed -i -E 's/^name:.*/name: '"${CONDA_ENV_NAME}"'/' /tmp/environment.yml || true
#    Option B (alternative) : retirer la ligne name:
# RUN sed -i -E '/^name:/d' /tmp/environment.yml || true
