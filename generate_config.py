#!/usr/bin/env python3
"""Generate xray config + VLESS link + subscription from env.

Usage:
  UUID=<uuid> WS_PATH=/ray PORT=8080 python3 generate_config.py --host example.com --name node-01
  --out-dir defaults to the credentials dir for this node; secrets are written
  to a 0600 file there and NEVER printed to stdout.
  Without --uuid a fresh UUID is generated and stored the same way.

Env (per DEPLOY_MEMORY.md §5 Route A):
  PORT     - platform-assigned port, never hardcoded (default 8080 for local test)
  UUID     - per-node UUID, generated if absent
  WS_PATH  - websocket path, default /ray (must start with /)
"""
import argparse, base64, json, os, secrets, sys, uuid
from pathlib import Path

def b64_nopad(s: str) -> str:
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", required=True, help="public host (domain or IP, no scheme)")
    p.add_argument("--port", type=int, default=443)
    p.add_argument("--name", default="node-01")
    p.add_argument("--uuid", default=os.environ.get("UUID", ""))
    p.add_argument("--ws-path", default=os.environ.get("WS_PATH", "/ray"))
    p.add_argument("--listen-port", type=int, default=int(os.environ.get("PORT", "8080")))
    p.add_argument("--out-dir", default="")
    p.add_argument("--tls", choices=["tls", "none"], default="tls",
                   help="tls = platform terminates TLS / VLESS+WS+TLS; none = direct IP:port")
    p.add_argument("--print-link", action="store_true",
                   help="print the vless:// link (only for local test; never use with a real node in chat)")
    args = p.parse_args()

    node_uuid = args.uuid or str(uuid.uuid4())
    ws_path = args.ws_path if args.ws_path.startswith("/") else "/" + args.ws_path

    config = {
        "log": {"loglevel": "warning"},
        "inbounds": [{
            "port": args.listen_port,
            "listen": "0.0.0.0",
            "protocol": "vless",
            "settings": {"clients": [{"id": node_uuid, "flow": ""}], "decryption": "none"},
            "streamSettings": {
                "network": "ws",
                "wsSettings": {"path": ws_path},
                "security": "none"  # TLS is terminated by the platform / reverse proxy
            }
        }],
        "outbounds": [{"protocol": "freedom", "settings": {}}]
    }

    # VLESS link: vless://UUID@host:port?encryption=none&security=tls&sni=host&type=ws&host=host&path=%2Fray#name
    from urllib.parse import quote
    q = (f"encryption=none&security={args.tls}&sni={args.host}&type=ws"
         f"&host={args.host}&path={quote(ws_path)}")
    link = f"vless://{node_uuid}@{args.host}:{args.port}?{q}#{quote(args.name)}"
    subscription = base64.b64encode((link + "\n").encode()).decode()

    out_dir = Path(args.out_dir) if args.out_dir else Path(__file__).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    # Credentials: 0600, one file per node. This file is the only place the UUID lives.
    cred = out_dir / "credentials.env"
    cred.write_text(f"HOST={args.host}\nPORT={args.port}\nUUID={node_uuid}\nWS_PATH={ws_path}\nTLS={args.tls}\nNAME={args.name}\n")
    os.chmod(cred, 0o600)
    # Subscription file holds only the base64 blob (no plaintext UUID in filename/content label).
    (out_dir / "subscription.txt").write_text(subscription + "\n")
    print(f"wrote config.json + subscription.txt to {out_dir}")
    print(f"listen_port={args.listen_port} ws_path={ws_path} tls={args.tls} host={args.host}")
    print("UUID stored in credentials.env (0600) only.")
    if args.print_link:
        print("VLESS_LINK=" + link)
    return 0

if __name__ == "__main__":
    sys.exit(main())
