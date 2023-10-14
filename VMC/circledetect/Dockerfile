FROM nvcr.io/nvidia/l4t-ml:r32.6.1-py3

# Fix numpy issues
ENV OPENBLAS_CORETYPE AARCH64

# Needed as some repo certs are expired in the base image
RUN apt-get update -y || true \
 && apt-get install -y ca-certificates software-properties-common && update-ca-certificates

# Install Python newer than 3.6
RUN add-apt-repository ppa:deadsnakes/ppa \
 && apt-get update -y
# https://askubuntu.com/a/1297198
# libssl is needed for MQTT libraries
RUN apt-get install -y \
    python3.9 \
    python3.9-dev \
    python3.9-distutils \
    python3-pip \
    libssl-dev
RUN python3.9 -m pip install pip wheel setuptools --upgrade

WORKDIR /app

# RUN git clone https://github.com/NVIDIA-AI-IOT/isaac_ros_apriltag \
#  && cd isaac_ros_apriltag \
#  && git checkout v0.9.0-ea1 \
#  && cp -r isaac_ros_apriltag/nvapriltags/lib_aarch64_jetpack44 ../c/libraries/lib_aarch64_jetpack44


COPY python/requirements.txt python/requirements.txt
RUN python3.9 -m pip install -r python/requirements.txt
RUN ls /dev/*
COPY . .
CMD ["python3.9", "python/circle_detect.py"]
