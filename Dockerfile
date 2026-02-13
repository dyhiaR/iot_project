FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
  git build-essential cmake ninja-build python3 python3-pip \
  libreadline-dev libncurses-dev iproute2 iputils-ping \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt
RUN git clone --recurse-submodules https://github.com/openthread/openthread.git
WORKDIR /opt/openthread
RUN ./script/cmake-build posix -DOT_POSIX_CONFIG_BORDER_ROUTING=OFF

RUN pip3 install --no-cache-dir --break-system-packages aiocoap

WORKDIR /work
COPY sensors/ /work/sensors/
COPY scripts/ /work/scripts/
RUN chmod +x /work/scripts/*.sh

CMD ["bash"]
