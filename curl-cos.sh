curl -v -H "Authorization: HMAC <HMAC_ACCESS_KEY>" \
     -H "x-amz-content-sha256: UNSIGNED-PAYLOAD" \
     "https://bu0021009393.s3.direct.eu-fr2.cloud-object-storage.appdomain.cloud:4229"
     
pip uninstall -y mmcv mmcv-full mmdet mmengine torchvision torchaudio torch

pip install --no-cache-dir torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 \
  --index-url https://download.pytorch.org/whl/cu121

pip install --no-cache-dir mmengine==0.10.4 mmcv==2.2.0 mmdet==3.3.0

python -c "import sys; print(sys.executable)"
python -m pip -V
python -m pip uninstall -y mmcv mmcv-full mmdet mmengine openmim torch torchvision torchaudio
python -m pip cache purge
# PyTorch cu121
python -m pip install --no-cache-dir \
  torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 \
  --index-url https://download.pytorch.org/whl/cu121

# OpenMMLab via openmim pour récupérer le bon wheel binaire mmcv
python -m pip install -U --no-cache-dir openmim
python -m pip install --no-cache-dir mmengine==0.10.4
mim install "mmcv==2.2.0" -f https://download.openmmlab.com/mmcv/cu121/torch2.3/index.html
python -m pip install --no-cache-dir mmdet==3.3.0 opencv-python-headless<5 pycocotools>=2.0.7
cuda 118
# PyTorch cu118
python -m pip install --no-cache-dir \
  torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2 \
  --index-url https://download.pytorch.org/whl/cu118

python -m pip install -U --no-cache-dir openmim
python -m pip install --no-cache-dir mmengine==0.10.4
mim install "mmcv==2.1.0" -f https://download.openmmlab.com/mmcv/cu118/torch2.2/index.html
python -m pip install --no-cache-dir mmdet==3.3.0 opencv-python-headless<5 pycocotools>=2.0.7
nvcc --version        # indique la version du toolkit (s’il est présent)
cat /usr/local/cuda/version.txt  # autre source si nvcc absent
readlink -f /usr/local/cuda  
