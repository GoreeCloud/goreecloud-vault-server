#!/usr/bin/env python3
from pathlib import Path

path = Path("docker/DockerSettings.yaml")
text = path.read_text(encoding="utf-8")
replacements = {
    'rust_version: 1.97.1 # Rust version to be used\n': 'rust_version: 1.97.1 # Rust version to be used\nrust_image_digest: "sha256:8e8cf8f7fd54a2d23d5a743b3a03f56e26b6c774276c33fa0595111704ebb15c" # rust:1.97.1-slim-trixie OCI index\n',
    'debian_version: trixie # Debian release name to be used\n': 'debian_version: trixie # Debian release name to be used\ndebian_image_digest: "sha256:3a39a0592364683e6bab97937b72cad5a8fa6dcbbee90edb3bb48c7f8e94f258" # debian:trixie-slim OCI index\n',
    '    image: "docker.io/library/rust:{{rust_version}}-slim-{{debian_version}}"\n': '    image: "docker.io/library/rust:{{rust_version}}-slim-{{debian_version}}@{{rust_image_digest}}"\n',
    '  debian: "docker.io/library/debian:{{debian_version}}-slim"\n': '  debian: "docker.io/library/debian:{{debian_version}}-slim@{{debian_image_digest}}"\n',
}
for old, new in replacements.items():
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one DockerSettings target, found {count}: {old!r}")
    text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
