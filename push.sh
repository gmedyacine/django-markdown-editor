# --- Contexte Artifactory ---
ARG ART_HOST=repo.artifactory-dogen.group.echonext
ARG ART_BASE=https://${ART_HOST}/artifactory
# Repo PyPI "virtual" standard
ARG PIP_INDEX=${ART_BASE}/api/pypi/pypi/simple
# Repo PyPI (remote/virtual) pointant vers https://download.pytorch.org/whl/cu121/simple
# (nom d’exemple: torch-cu121)
ARG TORCH_INDEX=${ART_BASE}/api/pypi/torch-cu121/simple

# Creds pip pour root + domino
RUN mkdir -p /root/.pip /home/domino/.config/pip && \
    printf "[global]\nindex-url = %s\nextra-index-url = %s\ntrusted-host = %s\n" \
           "$PIP_INDEX" "$TORCH_INDEX" "$ART_HOST" | tee /root/.pip/pip.conf >/home/domino/.config/pip/pip.conf && \
    chown -R domino:domino /home/domino/.config/pip

# Install dans l’env conda déjà créé/activable
ARG CONDA_ENV_NAME=DWS-GPU
RUN . /opt/conda/etc/profile.d/conda.sh && conda activate "${CONDA_ENV_NAME}" && \
    python -m pip install --no-cache-dir \
        "torch==2.3.1" "torchvision==0.18.1" "torchaudio==2.3.1"
