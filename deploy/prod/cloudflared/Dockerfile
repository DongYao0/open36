FROM cloudflare/cloudflared:2024.12.2 AS cloudflared

FROM alpine:3.21.3
RUN apk add --no-cache ca-certificates \
    && addgroup -g 65532 cloudflared \
    && adduser -D -H -u 65532 -G cloudflared cloudflared \
    && mkdir -p /runtime \
    && chown cloudflared:cloudflared /runtime

COPY --from=cloudflared /usr/local/bin/cloudflared /usr/local/bin/cloudflared
COPY publish-url.sh /usr/local/bin/publish-url
RUN chmod 0755 /usr/local/bin/cloudflared /usr/local/bin/publish-url

USER cloudflared
ENTRYPOINT ["/usr/local/bin/publish-url"]
