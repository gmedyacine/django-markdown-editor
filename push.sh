SHELL ["/bin/bash","-lc"]
USER root
ARG CONDA_ENV_NAME=DWS-GPU

##### Choisir l’ABI Python cohérent avec vos wheels #####
# -> Si vous avez des wheels cp310, restez en Python 3.10 :
# RUN mamba env remove -n ${CONDA_ENV_NAME} -y || true \
#  && mamba create -n ${CONDA_ENV_NAME} python=3.10.13 -y
# -> Si vous avez des wheels cp311, gardez Python 3.11 :
# (commentez la ligne ci-dessous si l’env existe déjà)
RUN mamba env remove -n ${CONDA_ENV_NAME} -y || true \
 && mamba create -n ${CONDA_ENV_NAME} python=3.11.9 -y

##### Auth Artifactory pour ROOT (pas seulement /home/domino) #####
ARG DOCKERFILE_ARTIFACTORY_USERNAME
ARG DOCKERFILE_ARTIFACTORY_TOKEN
RUN printf "machine repo.artifactory-dogen.group.echonet\nlogin %s\npassword %s\n" \
    "$DOCKERFILE_ARTIFACTORY_USERNAME" "$DOCKERFILE_ARTIFACTORY_TOKEN" > /root/.netrc \
 && chmod 600 /root/.netrc

##### URLs internes Artifactory #####
# Dossiers qui CONTIENNENT les wheels .whl
ARG TORCH_WHEELS=https://repo.artifactory-dogen.group.echonet/artifactory/wheels/pytorch/cu121/
ARG MMCV_WHEELS=https://repo.artifactory-dogen.group.echonet/artifactory/openmmlab/mmcv/cu121/torch2.3/
# Index PyPI interne (pour mmengine/mmdet)
ARG PIP_INDEX_URL=https://repo.artifactory-dogen.group.echonet/artifactory/api/pypi/pypi/simple

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_DEFAULT_TIMEOUT=20
# rendre l’index interne par défaut pour root
RUN printf "[global]\nindex-url = %s\ntrusted-host = repo.artifactory-dogen.group.echonet\n" \
    "$PIP_INDEX_URL" > /etc/pip.conf

##### Nettoyage idempotent #####
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip uninstall -y \
      torch torchvision torchaudio mmcv mmcv-full mmengine mmdet || true \
 && /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip cache purge || true

##### 1) Torch 2.3.1 cu121 depuis vos wheels (offline) #####
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip install --no-cache-dir \
    --no-index --find-links ${TORCH_WHEELS} \
    torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1

##### 2) mmengine + mmdet via l’index PyPI Artifactory #####
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip install --no-cache-dir \
    mmengine==0.10.4 mmdet==3.3.0

##### 3) mmcv 2.1.0 depuis vos wheels (offline) #####
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip install --no-cache-dir --force-reinstall \
    --no-index --find-links ${MMCV_WHEELS} \
    mmcv==2.1.0

##### Sanity check #####
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python - <<'PY'
import sys, torch, mmcv, mmengine, mmdet
print(sys.version.split()[0])
print("torch", torch.__version__, "cuda", torch.version.cuda, "avail", torch.cuda.is_available())
print("mmcv", mmcv.__version__, "| mmengine", mmengine.__version__, "| mmdet", mmdet.__version__)
PY

USER domino
