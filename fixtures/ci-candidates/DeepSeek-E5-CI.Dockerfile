# CI derivative of the recorded E5 candidate.
# The repair is unchanged; only the Debian mirror and cacheable layer order
# are adapted for repeatable builds on the course server.
FROM python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f
WORKDIR /work
RUN sed -i 's|http://deb.debian.org|http://mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get -o Acquire::Retries=5 -o Acquire::http::Timeout=30 update \
    && apt-get -o Acquire::Retries=5 -o Acquire::http::Timeout=30 install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY main.c Makefile ./
RUN make
CMD ["./hello"]
