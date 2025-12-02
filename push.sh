ARG CONDA_ENV_NAME=DWS-GPU
ENV CONDA_ENV_NAME=${CONDA_ENV_NAME}
ENV CONDA_PREFIX=/opt/conda/envs/${CONDA_ENV_NAME}
ARG ART_URL=https://repo.artifactory-dogen.group.echonet/artifactory

# (optionnel) éviter les prompts conda
ENV CONDA_ALWAYS_YES=true PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_DEFAULT_TIMEOUT=70

# --- Nettoyage du YAML (supprime name/prefix + anciennes lignes torch*) ---
RUN sed -i -E '/^[[:space:]]*(name|prefix):/d; \
               /^[[:space:]]*pytorch([:=]|$)/d; \
               /^[[:space:]]*torchvision([:=]|$)/d; \
               /^[[:space:]]*torchaudio([:=]|$)/d' /tmp/environment.yml

# --- Forcer les channels conda sur Artifactory uniquement ---
RUN /opt/conda/bin/conda config --set ssl_verify false && \
    (/opt/conda/bin/conda config --remove-key channels || true) && \
    (/opt/conda/bin/conda config --remove-key default_channels || true) && \
    /opt/conda/bin/conda config --add channels "${ART_URL}/api/conda/conda-forge" && \
    /opt/conda/bin/conda config --add channels "${ART_URL}/api/conda/conda-main" && \
    /opt/conda/bin/conda config --set show_channel_urls true

# --- 1) Remove dans un RUN séparé (tolère l’absence) ---
RUN /opt/conda/bin/conda env remove -p "${CONDA_PREFIX}" -y || true

# --- 2) Create dans un RUN séparé (les bons arguments ici seulement) ---
RUN /opt/conda/bin/conda env create -p "${CONDA_PREFIX}" -f /tmp/environment.yml \
    --override-channels \
    -c "${ART_URL}/api/conda/conda-forge" \
    -c "${ART_URL}/api/conda/conda-main" \
    -q

# --- 3) Nettoyage cache conda ---
RUN /opt/conda/bin/conda clean -y --all
