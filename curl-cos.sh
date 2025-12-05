# 6) Stack OpenMMLab + easyocr + onnxruntime dans DWS-GPU
RUN . /opt/conda/etc/profile.d/conda.sh && conda activate "${CONDA_ENV_NAME}" && \
    PIP_BIN="/opt/conda/envs/${CONDA_ENV_NAME}/bin/pip" && \
    \
    # 6.1 mmengine / mmcv / mmdet (versions compatibles)
    "$PIP_BIN" install --no-cache-dir \
        "mmengine==0.10.4" \
        "mmcv==2.1.0" \
        "mmdet==3.3.0" && \
    \
    # 6.2 easyocr sans deps, puis deps explicites
    "$PIP_BIN" install --no-cache-dir --no-deps "easyocr==1.7.1" && \
    "$PIP_BIN" install --no-cache-dir \
        "opencv-python-headless>=4.9.0.80" \
        "scikit-image>=0.22.0" \
        "shapely>=2.0.2" \
        "pyclipper>=1.3.0.post5" \
        "python-bidi>=0.4.2" \
        "PyYAML>=6.0.1" \
        "scipy>=1.13.0" \
        "numpy>=1.26.4" && \
    \
    # 6.3 onnxruntime : GPU si dispo, sinon CPU
    ( "$PIP_BIN" install --no-cache-dir "onnxruntime-gpu==1.17.3" \
      || "$PIP_BIN" install --no-cache-dir "onnxruntime==1.17.3" )
