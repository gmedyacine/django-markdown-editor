# --- Vars ---
ARG CONDA_ENV_NAME=DWS-GPU
ENV CONDA_ENV_NAME=${CONDA_ENV_NAME}
ENV CONDA_PREFIX=/opt/conda/envs/${CONDA_ENV_NAME}
ARG ART_URL=https://repo.artifactory-dogen.group.echonet/artifactory
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_DEFAULT_TIMEOUT=70

# --- Nettoyage du YAML: enlève name/prefix et paquets torch* du fichier ---
RUN sed -i -E '/^[[:space:]]*(name|prefix):/d; \
               /^[[:space:]]*pytorch([:=]|$)/d; \
               /^[[:space:]]*torchvision([:=]|$)/d; \
               /^[[:space:]]*torchaudio([:=]|$)/d' /tmp/environment.yml

# --- Conda: forcer les channels Artifactory (PAS d’options -c sur env create) ---
RUN /opt/conda/bin/conda config --set ssl_verify false && \
    (/opt/conda/bin/conda config --remove-key channels || true) && \
    (/opt/conda/bin/conda config --remove-key default_channels || true) && \
    /opt/conda/bin/conda config --add channels "${ART_URL}/api/conda/conda-forge" && \
    /opt/conda/bin/conda config --add channels "${ART_URL}/api/conda/conda-main" && \
    /opt/conda/bin/conda config --set show_channel_urls true

# --- Remove éventuel (toléré) puis création propre de l’env ---
RUN /opt/conda/bin/conda env remove -p "${CONDA_PREFIX}" -y || true
RUN /opt/conda/bin/conda env create -p "${CONDA_PREFIX}" -f /tmp/environment.yml -q
RUN /opt/conda/bin/conda clean -y --all
