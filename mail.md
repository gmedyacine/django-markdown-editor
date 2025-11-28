To stabilize Env 5.1 with GPU support, please approve the following version matrix (CUDA 12.1). I’ll apply it and run validation (imports + torch.cuda.is_available() + small CUDA op).

Component	Target Version / Requirement
Python	3.10–3.11
CUDA (wheels)	cu121
NVIDIA Driver (node)	≥ 535
PyTorch	2.3.1 (cu121)
torchvision	0.18.1
torchaudio	2.3.1

| Cible GPU                  | Python    |   PyTorch | CUDA (wheel) | torchvision | torchaudio |  **mmcv** | **mmengine** | **mmdet** | Remarques                                                  |
| -------------------------- | --------- | --------: | ------------ | ----------: | ---------: | --------: | -----------: | --------: | ---------------------------------------------------------- |
| **Option A – Recommandée** | 3.10–3.11 | **2.3.1** | **cu121**    |      0.18.1 |      2.3.1 | **2.2.0** |   **0.10.4** | **3.3.0** | Combo validé; évitez mmcv 2.2.6 qui casse avec mmdet 3.3.0 |
| Option B (si nœud en 11.8) | 3.10–3.11 |     2.2.2 | cu118        |      0.17.2 |      2.2.2 | **2.1.0** |   **0.10.4** | **3.3.0** | À utiliser seulement si votre nœud est CUDA 11.8           |

