curl -v -H "Authorization: HMAC <HMAC_ACCESS_KEY>" \
     -H "x-amz-content-sha256: UNSIGNED-PAYLOAD" \
     "https://bu0021009393.s3.direct.eu-fr2.cloud-object-storage.appdomain.cloud:4229"
     
pip uninstall -y mmcv mmcv-full mmdet mmengine torchvision torchaudio torch

pip install --no-cache-dir torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 \
  --index-url https://download.pytorch.org/whl/cu121

pip install --no-cache-dir mmengine==0.10.4 mmcv==2.2.0 mmdet==3.3.0
