SHELL ["/bin/bash","-lc"]
USER root
ARG CONDA_ENV_NAME=DWS-GPU

# ↓↓↓ REMPLACE ces 2 URLs par vos miroirs internes ↓↓↓
ARG TORCH_WHEELS=https://<ARTIFACTORY>/wheels/pytorch/cu121/
ARG MMCV_WHEELS=https://<ARTIFACTORY>/openmmlab/mmcv/cu121/torch2.3/

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_DEFAULT_TIMEOUT=15

# 0) Nettoyage idempotent (pas obligatoire mais propre)
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip uninstall -y \
      torch torchvision torchaudio mmcv mmcv-full mmdet mmengine || true && \
    /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip cache purge || true

# 1) Fichier requirements PIP **100% offline** (on guide pip vers Artifactory)
RUN cat > /tmp/pip.txt <<'REQ'
--no-index
--find-links ${TORCH_WHEELS}
torch==2.3.1
torchvision==0.18.1
torchaudio==2.3.1

mmengine==0.10.4
mmdet==3.3.0

--find-links ${MMCV_WHEELS}
mmcv==2.1.0
REQ

# 2) Installation pip depuis Artifactory (une seule commande, pas de boucles)
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip install --no-cache-dir -r /tmp/pip.txt

# 3) Sanity check pendant build
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python - <<'PY'
import torch, mmcv, mmengine, mmdet
print("torch:", torch.__version__, "cuda:", torch.version.cuda, "avail:", torch.cuda.is_available())
print("mmcv:", mmcv.__version__, "| mmengine:", mmengine.__version__, "| mmdet:", mmdet.__version__)
PY

USER domino
