#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/deploy/compose.production.yaml"
ENV_FILE="$(mktemp)"
MODEL_FILE="$(mktemp)"
trap 'rm -f "${ENV_FILE}" "${MODEL_FILE}"' EXIT

cat > "${ENV_FILE}" <<'EOF'
GOREVAULT_IMAGE=ghcr.io/goreecloud/goreevault-server@sha256:1111111111111111111111111111111111111111111111111111111111111111
POSTGRES_IMAGE=docker.io/library/postgres@sha256:2222222222222222222222222222222222222222222222222222222222222222
GOREVAULT_UID=10001
GOREVAULT_GID=10001
GOREVAULT_DOMAIN=https://vault.goreecloud.invalid
GOREVAULT_HTTP_PORT=8080
POSTGRES_DB=goreevault
POSTGRES_USER=goreevault
POSTGRES_PASSWORD=validation-only-password
SIGNUPS_ALLOWED=false
INVITATIONS_ALLOWED=true
EOF

docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" config -q
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" config --format json > "${MODEL_FILE}"

python3 - "${MODEL_FILE}" <<'PY'
import json
import re
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    model = json.load(handle)

services = model.get("services", {})
server = services.get("server")
postgres = services.get("postgres")
data_init = services.get("data-init")
assert isinstance(server, dict), "production compose must define server service"
assert isinstance(postgres, dict), "production compose must define postgres service"
assert isinstance(data_init, dict), "production compose must define data-init service"

immutable = re.compile(r"@sha256:[0-9a-f]{64}$")
for name, service in (("server", server), ("data-init", data_init), ("postgres", postgres)):
    image = service.get("image", "")
    assert immutable.search(image), f"{name} image must resolve to an immutable sha256 digest: {image!r}"
    assert "build" not in service, f"{name} must not build source in production"

assert server["image"] == data_init["image"], "data-init must use the exact GoreeVault server image digest"
assert not postgres.get("ports"), "PostgreSQL must not publish a host port"
backend = model.get("networks", {}).get("goreevault-backend", {})
assert backend.get("internal") is True, "goreevault-backend must remain an internal network"
assert "goreevault-backend" in postgres.get("networks", {}), "PostgreSQL must use goreevault-backend"

ports = server.get("ports", [])
assert len(ports) == 1, "server must publish exactly one loopback HTTP port"
port = ports[0]
assert port.get("host_ip") == "127.0.0.1", "server HTTP port must bind only to loopback"
assert int(port.get("target", 0)) == 8080, "server container HTTP target must remain unprivileged port 8080"

user = str(server.get("user", ""))
assert user not in {"", "0", "0:0", "root"}, "server must run as an explicit non-root user"
assert user == "10001:10001", f"validation model expected dedicated GoreeVault UID/GID, got {user!r}"
assert server.get("read_only") is True, "server root filesystem must remain read-only"
assert "ALL" in server.get("cap_drop", []), "server must drop all Linux capabilities"
assert "no-new-privileges:true" in server.get("security_opt", []), "server must retain no-new-privileges"
assert server.get("tmpfs"), "server must have an explicit writable tmpfs instead of a writable root filesystem"

env = server.get("environment", {})
assert env.get("SIGNUPS_ALLOWED") == "false", "production registration must default closed"
assert env.get("DOMAIN", "").startswith("https://"), "production DOMAIN must use HTTPS"
assert str(env.get("ROCKET_PORT")) == "8080", "production Rocket listener must use unprivileged port 8080"
assert env.get("DATA_FOLDER") == "/data", "production data folder must remain /data"
assert "goreevault-backend" in server.get("networks", {}), "server must reach the internal backend"

assert str(data_init.get("user")) == "0:0", "data initializer must declare its short-lived root identity explicitly"
assert data_init.get("network_mode") == "none", "data initializer must not have network access"
assert data_init.get("read_only") is True, "data initializer root filesystem must remain read-only"
assert "ALL" in data_init.get("cap_drop", []), "data initializer must start from a drop-all capability set"
assert set(data_init.get("cap_add", [])) <= {"CHOWN", "FOWNER"}, "data initializer has unexpected capabilities"
assert "CHOWN" in data_init.get("cap_add", []), "data initializer requires only the CHOWN capability for /data"
assert "no-new-privileges:true" in data_init.get("security_opt", []), "data initializer must retain no-new-privileges"

server_depends = server.get("depends_on", {})
assert server_depends.get("data-init", {}).get("condition") == "service_completed_successfully", (
    "server must not start before data-init completes successfully"
)
assert server_depends.get("postgres", {}).get("condition") == "service_healthy", (
    "server must not start before PostgreSQL is healthy"
)

print("GoreeVault production Compose invariants validated.")
PY
