# Use CUDA-enabled base image for PyTorch support
FROM nvidia/cuda:12.0.0-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create workspace directory
WORKDIR /workspace

# Copy requirements file
COPY ["Function .py Storage/requirements.txt", "/workspace/requirements.txt"]

# Install Python packages
RUN pip3 install --no-cache-dir jupyter jupyterlab && \
    pip3 install --no-cache-dir -r requirements.txt

# Install PyTorch with CUDA support
RUN pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu120

# Create directories for mounting
RUN mkdir -p /workspace/data /workspace/notebooks /workspace/functions

# Copy custom modules (assuming they're in Function.py Storage)
COPY ["Function .py Storage/*.py", "/workspace/functions/"]

# Expose Jupyter port
EXPOSE 8888

# Set up Jupyter configuration
RUN jupyter notebook --generate-config && \
    echo "c.NotebookApp.ip = '0.0.0.0'" >> /root/.jupyter/jupyter_notebook_config.py && \
    echo "c.NotebookApp.allow_root = True" >> /root/.jupyter/jupyter_notebook_config.py && \
    echo "c.NotebookApp.open_browser = False" >> /root/.jupyter/jupyter_notebook_config.py

# Start Jupyter
CMD ["jupyter", "lab", "--allow-root", "--ip=0.0.0.0", "--port=8888", "--no-browser"] 