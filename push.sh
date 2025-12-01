SHELL ["/bin/bash","-lc"]
USER root
ARG CONDA_ENV_NAME=DWS-GPU

# ====== URLs internes (à garder sur votre Artifactory) ======
# Dossiers qui CONTIENNENT les wheels .whl
ARG TORCH_WHEELS=https://repo.artifactory-dogen.group.echonet/artifactory/wheels/pytorch/cu121/
ARG MMCV_WHEELS=https://repo.artifactory-dogen.group.echonet/artifactory/openmmlab/mmcv/cu121/torch2.3/

# Couper les appels externes pip
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_DEFAULT_TIMEOUT=15

# Purge idempotente
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip uninstall -y \
      torch torchvision torchaudio mmcv mmcv-full mmengine mmdet || true && \
    /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip cache purge || true

# Requirements "offline" pointant UNIQUEMENT vers Artifactory (variables EXPANSÉES)
RUN cat > /tmp/pip-offline.txt <<EOF
--no-index
--find-links ${TORCH_WHEELS}
--find-links ${MMCV_WHEELS}

torch==2.3.1
torchvision==0.18.1
torchaudio==2.3.1

mmengine==0.10.4
mmdet==3.3.0
mmcv==2.1.0
EOF

# Install unique (aucun egress)
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python -m pip install --no-cache-dir \
    -r /tmp/pip-offline.txt

# Sanity check log build
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python - <<'PY'
import torch, mmcv, mmengine, mmdet
print("torch:", torch.__version__, "cuda:", torch.version.cuda, "avail:", torch.cuda.is_available())
print("mmcv:", mmcv.__version__, "| mmengine:", mmengine.__version__, "| mmdet:", mmdet.__version__)
PY

USER domino
