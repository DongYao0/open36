FROM alpine:3.22

ARG FRP_VERSION=0.71.0
ARG FRP_ARCHIVE_SHA256=84f27e39f11169f7adcef8e8b70c9329de17747b1f14dad9fb95eef5682ea716

RUN apk add --no-cache ca-certificates curl

RUN curl --fail --location --retry 3 \
      --connect-timeout 10 --max-time 120 \
      --output /tmp/frp.tar.gz \
      "https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/frp_${FRP_VERSION}_linux_amd64.tar.gz" \
    && echo "${FRP_ARCHIVE_SHA256}  /tmp/frp.tar.gz" | sha256sum -c - \
    && tar -xzf /tmp/frp.tar.gz -C /tmp \
    && install -m 0755 \
      "/tmp/frp_${FRP_VERSION}_linux_amd64/frpc" /usr/local/bin/frpc \
    && rm -rf /tmp/frp.tar.gz "/tmp/frp_${FRP_VERSION}_linux_amd64"

COPY healthcheck.sh /usr/local/bin/frpc-healthcheck

RUN chmod 0755 /usr/local/bin/frpc /usr/local/bin/frpc-healthcheck \
    && addgroup -S -g 1001 frpc \
    && adduser -S -D -H -u 1001 -G frpc frpc

USER 1001:1001
ENTRYPOINT ["/usr/local/bin/frpc"]
