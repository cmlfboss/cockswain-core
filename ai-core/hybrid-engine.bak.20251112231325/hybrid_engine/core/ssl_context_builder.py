import ssl
import contextlib
from pathlib import Path
import json

DEFAULT_SSL_CFG = {
    "enable": True,
    "cert_file": "",
    "key_file": "",
    "check_hostname": False,
    "verify_mode": "CERT_NONE"
}

def _verify_mode(name: str) -> ssl.VerifyMode:
    return getattr(ssl, name, ssl.CERT_NONE)

def load_ssl_config(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return DEFAULT_SSL_CFG
    try:
        return {**DEFAULT_SSL_CFG, **json.loads(p.read_text(encoding="utf-8"))}
    except Exception:
        return DEFAULT_SSL_CFG

def build_ssl_context(cert_file: str, key_file: str, check_hostname=False, verify_mode="CERT_NONE"):
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    if cert_file and key_file and Path(cert_file).exists() and Path(key_file).exists():
        ctx.load_cert_chain(certfile=cert_file, keyfile=key_file)
    ctx.check_hostname = bool(check_hostname)
    ctx.verify_mode = _verify_mode(verify_mode)
    return ctx

@contextlib.asynccontextmanager
async def secure_connection(reader, writer):
    try:
        yield reader, writer
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
