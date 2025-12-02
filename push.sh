### >>> VENV INSTALL FROM YAML FILE <<<

# On travaille en tant que 'domino' et on définit d'abord les ARG utilisés
USER domino
ARG CONDA_ENV_NAME=DWS-GPU
ARG PY_MAJOR=3.11

# URLs Artifactory (adapter si besoin)
ARG ART_URL=https://repo.artifactory-dogen.group.echonet/artifactory
ARG DOCKERFILE_ARTIFACTORY_USERNAME
ARG DOCKERFILE_ARTIFACTORY_TOKEN

# Auth + config pour L'UTILISATEUR COURANT (domino) AVANT tout mamba/pip
RUN printf "machine repo.artifactory-dogen.group.echonet\nlogin %s\npassword %s\n" \
    "$DOCKERFILE_ARTIFACTORY_USERNAME" "$DOCKERFILE_ARTIFACTORY_TOKEN" > ~/.netrc \
 && mkdir -p ~/.config/pip \
 && printf "[global]\nindex-url = %s/api/pypi/pypi/simple\ntrusted-host = repo.artifactory-dogen.group.echonet\n" \
    "$ART_URL" > ~/.config/pip/pip.conf \
 && printf "channels:\n  - conda-forge\n  - defaults\nchannel_alias: %s/api/conda\nshow_channel_urls: true\ndefault_channels:\n  - %s/api/conda/conda-forge\n  - %s/api/conda/conda-main\n" \
    "$ART_URL" "$ART_URL" "$ART_URL" > ~/.condarc

# Si l'env n'existe pas, on le crée (évite l'erreur 'No prefix …')
RUN test -d "/opt/conda/envs/${CONDA_ENV_NAME}" || mamba create -y -n "${CONDA_ENV_NAME}" "python=${PY_MAJOR}"

# On retire Torch du YAML si on va l’installer par pip/offline
RUN sed -E -i '/^[[:space:]]*-[[:space:]]*(pytorch|torchvision|torchaudio|pytorch-cuda)/d' /tmp/environment.yml || true

# Mise à jour de l'env via Artifactory (pas d'appel internet)
RUN mamba env update -n "${CONDA_ENV_NAME}" -f /tmp/environment.yml --prune \
    --override-channels \
    -c ${ART_URL}/api/conda/conda-forge \
    -c ${ART_URL}/api/conda/conda-main

# --- Torch stack cu121 (wheels internes) ---
# Adapte ces chemins à tes repos de wheels
ARG TORCH_WHEELS=${ART_URL}/wheels/pytorch/cu121/torch2.3/cp311/
ARG MMCV_WHEELS=${ART_URL}/wheels/openmmlab/mmcv/cu121/torch2.3/cp311/

RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/pip install --no-cache-dir --no-index \
    --find-links "${TORCH_WHEELS}" \
    torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1

RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/pip install --no-cache-dir --no-index \
    --find-links "${MMCV_WHEELS}" \
    mmcv==2.1.0

# Paquets python restants en ligne (Artifactory pip)
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/pip install --no-cache-dir \
    mmengine==0.10.4 mmdet==3.3.0

# Sanity check (échoue le build si versions incorrectes)
RUN /opt/conda/envs/${CONDA_ENV_NAME}/bin/python - <<'PY'
import torch, mmcv, mmengine, mmdet
print("Torch:", torch.__version__, "CUDA:", torch.version.cuda, "avail:", torch.cuda.is_available())
assert torch.__version__.startswith("2.3."), torch.__version__
assert mmcv.__version__.startswith("2.1."), mmcv.__version__
assert mmengine.__version__.startswith("0.10."), mmengine.__version__
assert mmdet.__version__.startswith("3.3."), mmdet.__version__
PY

# (Optionnel) nettoyage côté root APRÈS installation
USER root
RUN rm -rf /var/lib/apt/lists/* /var/cache/apt/* /etc/apt/auth.conf.d/artifactory.conf \
           /home/domino/.config/pip/pip.conf /home/domino/.condarc
USER domino
