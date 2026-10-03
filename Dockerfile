FROM ros:jazzy-ros-base-noble

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-demo-nodes-cpp \
    ros-jazzy-ros-gz \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
CMD ["bash"]