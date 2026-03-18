#!/bin/bash
set -e

pip install -r requirements.txt

# openwakeword pulls in tflite-runtime which isn't available on aarch64.
# We only use the onnx backend, so install without deps.
pip install --no-deps openwakeword

# Download openwakeword's bundled preprocessing models (melspectrogram, etc.)
python -c "from openwakeword.utils import download_models; download_models()"
