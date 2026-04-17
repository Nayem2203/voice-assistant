#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
# This ensures the server can handle audio processing
apt-get update && apt-get install -y ffmpeg