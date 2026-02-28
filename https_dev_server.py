import os
import sys
from pathlib import Path

import trustme
import uvicorn


def _ensure_cert_files(cert_dir: Path) -> tuple[Path, Path]:
    cert_dir.mkdir(parents=True, exist_ok=True)
    cert_path = cert_dir / "dev_cert.pem"
    key_path = cert_dir / "dev_key.pem"

    if cert_path.exists() and key_path.exists():
        return cert_path, key_path

    ca = trustme.CA()
    server_cert = ca.issue_cert("127.0.0.1", "localhost")
    server_cert.cert_chain_pems[0].write_to_path(cert_path)
    server_cert.private_key_pem.write_to_path(key_path)

    return cert_path, key_path


def _parse_addrport(args: list[str]) -> tuple[str, int]:
    addrport = None
    for arg in args:
        if not arg.startswith("-"):
            addrport = arg
            break

    if not addrport:
        return "127.0.0.1", 8000

    if ":" in addrport:
        host, port_str = addrport.rsplit(":", 1)
        host = host or "127.0.0.1"
        return host, int(port_str)

    return "127.0.0.1", int(addrport)


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    base_dir = Path(__file__).resolve().parent
    cert_dir = base_dir / ".devcert"
    cert_path, key_path = _ensure_cert_files(cert_dir)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zygotrip_project.settings")

    host, port = _parse_addrport(argv)

    uvicorn.run(
        "zygotrip_project.asgi:application",
        host=host,
        port=port,
        ssl_certfile=str(cert_path),
        ssl_keyfile=str(key_path),
        log_level="info",
    )


if __name__ == "__main__":
    main()
