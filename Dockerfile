# Debian-based xray image for Unikraft Cloud.
# Alpine/musl images fail on Unikraft (instance stops in ~1s, stop_code 1, no logs);
# Debian/glibc boots fine (verified with nginx:latest). Same entrypoint logic as
# the Alpine variant: reads PORT/UUID/WS_PATH from env, generates config, runs xray.
# No custom args needed at deploy time; the default ENTRYPOINT does the work.
FROM teddysun/xray:26.10.31 AS xray
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl python3 unzip && rm -rf /var/lib/apt/lists/*
COPY --from=xray /usr/bin/xray /usr/local/bin/xray
COPY generate_config.py entrypoint.sh /app/
WORKDIR /app
RUN chmod +x /app/entrypoint.sh && mkdir -p /app/data
ENV PORT=8080 WS_PATH=/ray
EXPOSE 8080
ENTRYPOINT ["/app/entrypoint.sh"]
