#!/bin/sh
# Route B entrypoint: 生成配置后拉起 xray（前台，容器活着进程就活着）。
# Route C 也可直接调本脚本：二进制放持久化目录，后台跑 + 日志重定向，
# 把内部端口 publish 成公开地址（见 README-kit.md）。
set -eu
APP_DIR="${APP_DIR:-/app}"
XRAY_BIN="${XRAY_BIN:-/usr/local/bin/xray}"
if [ -z "${UUID:-}" ]; then
  if [ -f "$APP_DIR/credentials.env" ]; then
    UUID="$(grep '^UUID=' "$APP_DIR/credentials.env" | cut -d= -f2)"
  else
    UUID="$(cat /proc/sys/kernel/random/uuid)"
    umask 077
    printf 'UUID=%s\nWS_PATH=%s\n' "$UUID" "${WS_PATH:-/ray}" > "$APP_DIR/credentials.env"
    chmod 600 "$APP_DIR/credentials.env"
  fi
fi
export UUID
python3 /app/generate_config.py \
  --host "${PUBLIC_HOST:-localhost}" \
  --port "${PUBLIC_PORT:-443}" \
  --name "${NODE_NAME:-node-01}" \
  --uuid "$UUID" \
  --ws-path "${WS_PATH:-/ray}" \
  --listen-port "${PORT:-8080}" \
  --out-dir "$APP_DIR"
echo "starting xray on PORT=${PORT:-8080} ws_path=${WS_PATH:-/ray}"
exec "$XRAY_BIN" run -config "$APP_DIR/config.json"
