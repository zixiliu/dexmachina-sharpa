# Base image: PyTorch 2.4.1 + CUDA 12.1. Ships Python 3.11 by default; we downgrade
# to 3.10 below because rl_games==1.6.1 requires `<3.11`.
FROM pytorch/pytorch:2.4.1-cuda12.1-cudnn9-devel

# Downgrade conda's Python to 3.10 so rl_games installs. This rebuilds the env.
RUN conda install -y python=3.10 && conda clean -afy

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        git ca-certificates build-essential \
        libegl1 libgl1 libgles2 libglu1-mesa libxext6 libxrender1 libxrandr2 \
        libsm6 libxi6 libxxf86vm1 libfontconfig1 libice6 \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Upgrade torch to 2.5.1 (matches dexmachina.yaml; Genesis 0.2.1 was tested with it).
RUN pip install --no-cache-dir \
        torch==2.5.1 torchvision==0.20.1 \
        --index-url https://download.pytorch.org/whl/cu121

# Pin numpy to 1.x (dexmachina.yaml has 1.26.4). Genesis's `tetgen` extension is
# compiled against the numpy 1.x ABI; numpy 2.x's renamed multiarray module breaks it.
RUN pip install --no-cache-dir "numpy<2"

# pkg_resources guard: wandb 0.12.21 (pinned in dexmachina.yaml) imports it.
# setuptools >= 81 removed pkg_resources, so we pin below that.
RUN pip install --no-cache-dir "setuptools<81"

WORKDIR /workspace

# Genesis (custom fork, pinned commit known to work with dexmachina).
RUN git clone https://github.com/MandiZhao/Genesis.git && \
    cd Genesis && git checkout e9df2d8 && \
    pip install --no-cache-dir libigl==2.5.1 && \
    pip install --no-cache-dir -e .

# rl_games (Mandi's fork, lives inside Genesis dir per upstream layout).
RUN cd Genesis && git clone https://github.com/MandiZhao/rl_games.git && \
    cd rl_games && git checkout 2c1a771 && \
    pip install --no-cache-dir -e .

# dexmachina runtime deps not bundled by Genesis / rl_games. Top-level pip deps
# from dexmachina.yaml that aren't transitive from anything else we install.
RUN pip install --no-cache-dir \
        wandb==0.12.21 \
        gymnasium==1.1.1 \
        gym==0.23.1 \
        ray==2.47.0 \
        tensorboardx==2.6.2.2 \
        dex-retargeting==0.5.0 \
        moviepy==1.0.3 \
        scikit-learn \
        seaborn==0.13.2 \
        trimesh==4.6.11 \
        mujoco==3.2.5 \
        pandas==2.3.0 \
        pyvista==0.45.2 \
        coacd==1.0.7

# dexmachina source + assets (retargeted .pt files + contact_retarget .npy +
# Sharpa URDFs/meshes + ARCTIC processed/objects). Ignored by .dockerignore:
# logs/, wandb/, Genesis/, dexmachina/.venv/.
COPY dexmachina/ /workspace/dexmachina-sharpa/dexmachina/
COPY setup.py README.md /workspace/dexmachina-sharpa/
WORKDIR /workspace/dexmachina-sharpa
RUN pip install --no-cache-dir -e .

# Force numpy back to <2 at the very end. Earlier `pip install` invocations
# (dexmachina + transitive deps from dex-retargeting/etc.) upgrade numpy to 2.x,
# which breaks Genesis's `tetgen` Cython extension. This is the final layer so
# nothing else can upgrade it. Bundle the RL extras here too since
# --force-reinstall above can knock out non-numpy packages.
RUN pip install --no-cache-dir --force-reinstall \
        "numpy<2" \
        "setuptools<81" \
        wandb==0.12.21 \
        gymnasium==1.1.1 \
        ray==2.47.0 \
        tensorboardx==2.6.2.2 \
        scikit-learn

WORKDIR /workspace/dexmachina-sharpa/dexmachina
ENV PYTHONPATH=/workspace/dexmachina-sharpa
