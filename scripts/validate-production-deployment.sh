#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/deploy/compose.production.yaml"
EXAMPLE_ENV="${ROOT_DIR}/deploy/.env.production.example"
ENV_FILE="$(mktemp)"
MODEL_FILE="$(mktemp)"
trap 'rm -f "${ENV_FILE}" "${MODEL_FILE}"' EXIT

[[ -f "${COMPOSE_FILE}" ]] || { echo "Missing ${COMPOSE_FILE}" >&2; exit 1; }
[[ -f "${EXAMPLE_ENV}" ]] || { echo "Missing ${EXAMPLE_ENV}" >&2; exit 1; }

grep -Fxq 'GOREVAULT_DOMAIN=https://vault.goreecloud.com' "${EXAMPLE_ENV}"
grep -Fxq 'SIGNUPS_ALLOWED=false' "${EXAMPLE_ENV}"
grep -Fxq 'ADMIN_TOKEN=' "${EXAMPLE_ENV}"
grep -Eq '^GOREVAULT_IMAGE=ghcr\.io/goreecloud/goreecloud-vault-server@sha256:' "${EXAMPLE_ENV}"

cat > "${ENV_FILE}" <<'EOF'
GOREVAULT_IMAGE=ghcr.io/goreecloud/goreecloud-vault-server@sha256:1111111111111111111111111111111111111111111111111111111111111111
POSTGRES_IMAGE=docker.io/library/postgres@sha256:2222222222222222222222222222222222222222222222222222222222222222
GOREVAULT_UID=10001
GOREVAULT_GID=10001
GOREVAULT_DOMAIN=https://vault.goreecloud.com
GOREVAULT_HTTP_PORT=8080
POSTGRES_DB=goreevault
POSTGRES_USER=goreevault
POSTGRES_PASSWORD=validation-only-password
SIGNUPS_ALLOWED=false
INVITATIONS_ALLOWED=true
ADMIN_TOKEN=
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
for name, service in (("server", server), ("postgres", postgres), ("data-init", data_init)):
    assert isinstance(service, dict), f"production compose must define {name} service"
    assert service.get("privileged") is not True, f"{name} must never be privileged"
    assert service.get("network_mode") != "host", f"{name} must never use host networking"
    assert service.get("pid") != "host", f"{name} must never share the host PID namespace"
    assert service.get("ipc") != "host", f"{name} must never share the host IPC namespace"
    assert not service.get("devices"), f"{name} must not receive host devices"

immutable = re.compile(r"@sha256:[0-9a-f]{64}$")
for name, service in (("server", server), ("data-init", data_init), ("postgres", postgres)):
    image = service.get("image", "")
    assert immutable.search(image), f"{name} image must resolve to an immutable sha256 digest: {image!r}"
    assert "build" not in service, f"{name} must not build source in production"

canonical_server_image = re.compile(r"^ghcr\.io/goreecloud/goreecloud-vault-server@sha256:[0-9a-f]{64}$")
assert canonical_server_image.fullmatch(server["image"]), (
    "server must use the canonical GoreeCloud Vault Server GHCR repository and an immutable digest"
)
assert server["image"] == data_init["image"], "data-init must use the exact GoreeCloud Vault Server image digest"

networks = model.get("networks", {})
backend = networks.get("goreevault-backend", {})
assert backend.get("internal") is True, "goreevault-backend must remain internal"
assert set(postgres.get("networks", {})) == {"goreevault-backend"}, "PostgreSQL must use only goreevault-backend"
assert {"goreevault-backend", "goreevault-edge"}.issubset(server.get("networks", {})), (
    "server must use the internal database network and the edge/egress network"
)
assert not postgres.get("ports"), "PostgreSQL must not publish a host port"

ports = server.get("ports", [])
assert len(ports) == 1, "server must publish exactly one HTTP port"
port = ports[0]
assert port.get("host_ip") == "127.0.0.1", "server HTTP port must bind only to IPv4 loopback"
assert int(port.get("target", 0)) == 8080, "server container target must remain unprivileged port 8080"
assert int(port.get("published", 0)) == 8080, "validation expects host loopback port 8080"

user = str(server.get("user", ""))
assert user == "10001:10001", f"server must run as the dedicated validation UID/GID, got {user!r}"
assert server.get("read_only") is True, "server root filesystem must remain read-only"
assert "ALL" in server.get("cap_drop", []), "server must drop all Linux capabilities"
assert not server.get("cap_add"), "server must not add Linux capabilities"
assert "no-new-privileges:true" in server.get("security_opt", []), "server must retain no-new-privileges"
assert server.get("tmpfs"), "server requires explicit writable tmpfs instead of a writable root filesystem"
assert int(server.get("pids_limit", 0)) == 256, "server must retain the bounded PID limit"

env = server.get("environment", {})
assert env.get("DOMAIN") == "https://vault.goreecloud.com", "production DOMAIN must be the canonical GoreeCloud Vault Server origin"
assert env.get("SIGNUPS_ALLOWED") == "false", "production registration must default closed"
assert env.get("ADMIN_TOKEN") in {None, ""}, "production admin surface must default disabled"
assert str(env.get("ROCKET_PORT")) == "8080", "Rocket must listen on unprivileged container port 8080"
assert env.get("ROCKET_ADDRESS") == "0.0.0.0", "container listener contract unexpectedly changed"
assert env.get("DATA_FOLDER") == "/data", "production data folder must remain /data"
assert str(env.get("DATABASE_URL", "")).startswith("postgresql://"), "production database must be PostgreSQL"

assert str(data_init.get("user")) == "0:0", "data initializer must declare its short-lived root identity"
assert data_init.get("network_mode") == "none", "data initializer must have no network access"
assert data_init.get("read_only") is True, "data initializer root filesystem must remain read-only"
assert "ALL" in data_init.get("cap_drop", []), "data initializer must begin from drop-all capabilities"
expected_init_caps = {"CHOWN", "DAC_OVERRIDE", "FOWNER"}
assert set(data_init.get("cap_add", [])) == expected_init_caps, "data initializer capability set drifted"
assert "no-new-privileges:true" in data_init.get("security_opt", []), "data initializer must retain no-new-privileges"

command = data_init.get("command", "")
command_text = "\n".join(command) if isinstance(command, list) else str(command)
chown_pos = command_text.find("chown -R")
marker_pos = command_text.find("touch")
assert chown_pos >= 0 and marker_pos >= 0 and chown_pos < marker_pos, (
    "data-init must create its success marker only after recursive ownership repair succeeds"
)

server_depends = server.get("depends_on", {})
assert server_depends.get("data-init", {}).get("condition") == "service_completed_successfully", (
    "server must not start before data-init completes successfully"
)
assert server_depends.get("postgres", {}).get("condition") == "service_healthy", (
    "server must not start before PostgreSQL is healthy"
)

print("GoreeCloud Vault Server production Compose invariants validated.")
PY
