---
component_id: "docker-desktop"
name: "Docker Desktop"
category: "Virtualization"
tier: "heavy"
status: "retired"
delivery_method: "vendor-download"
official_url: "https://www.docker.com/products/docker-desktop/"
replacement: "OrbStack"
replacement_url: "https://orbstack.dev/download"
verified_at: "2026-07-15"
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
---

# Docker Desktop retirement and OrbStack replacement

> [!warning] Irreversible operation
> Removing Docker Desktop permanently deletes its local containers, images (including user-built images), volumes, build cache, Kubernetes data, and settings. It does not delete remote registry images, `~/.docker`, or OrbStack data.

## Decision

Use OrbStack as the default local Docker backend on this Mac. It provides Docker-compatible containers and Linux machines with lower typical resource overhead than Docker Desktop. Do not leave Docker Desktop and OrbStack running as concurrent default backends.

## Safe detection and migration procedure

1. Inspect Docker Desktop-only paths and the OrbStack presence:

   ```sh
   python3 scripts/docker_desktop_cleanup.py inspect
   ```

2. If `orbstack_installed` is `false`, install OrbStack first—even on a new Mac where `docker_desktop_installed` is also `false`:

   ```sh
   brew install --cask orbstack
   open -a OrbStack
   ```

   Confirm that OrbStack starts normally before retiring Docker Desktop.

3. If `docker_desktop_installed` is `true`, explain exactly what will be lost and obtain explicit user confirmation. Then remove Docker Desktop:

   ```sh
   python3 scripts/docker_desktop_cleanup.py remove --confirm "REMOVE DOCKER DESKTOP DATA"
   ```

4. Run `inspect` again. Confirm that OrbStack is present and that `/Applications/Docker.app` is absent when Docker Desktop was detected. Only expected protected macOS metadata (if any) may remain.

The cleanup script uses Docker Desktop's official uninstaller first and targets only known Docker Desktop-owned paths. It deliberately preserves `~/.docker`, because Docker contexts and credentials there may also be used by OrbStack.

## OrbStack verification

OrbStack is ready for Docker work only when all checks below pass:

```sh
test -d /Applications/OrbStack.app
orbctl status
command -v docker
docker context show
docker version --format '{{.Server.Version}}'
python3 scripts/docker_desktop_cleanup.py inspect
```

Expected values are `Running` from `orbctl status`, `orbstack` from `docker context show`, and a non-empty server version. `command -v docker` is not sufficient by itself: it identifies the CLI location, not the active engine.

If the CLI is missing, OrbStack's supported CLI is at `~/.orbstack/bin/docker`. Offer this shell change only with user confirmation:

```sh
export PATH="$HOME/.orbstack/bin:$PATH"
```

Persisting it in `~/.zprofile` and creating the optional `/usr/local/bin/docker` JetBrains compatibility symlink both modify the local environment, so neither is automatic. Do not install Docker Desktop merely to obtain a `docker` command.

## Current Mac verification

| Check | Result |
|---|---|
| OrbStack | Installed and retained at `/Applications/OrbStack.app` |
| OrbStack service | Running |
| Docker CLI / context | `~/.orbstack/bin/docker`; active context `orbstack` |
| Docker Server | Version `29.4.0` responding through OrbStack |
| Docker Desktop app | Removed |
| Docker Desktop-local data | Removed: containers, images, volumes, build cache, Kubernetes data, and settings |
| Reclaimed space | Approximately 5.43 GB |
| Preserved | OrbStack and `~/.docker` |
| Residual | 4 KB macOS-protected metadata at `~/Library/Containers/com.docker.docker` |

## Verification

```sh
python3 scripts/docker_desktop_cleanup.py inspect
test ! -d /Applications/Docker.app
test -d /Applications/OrbStack.app
```

## References

- Docker Desktop stores Mac containers and images in a disk-image file: https://docs.docker.com/desktop/troubleshoot-and-support/faqs/macfaqs/
- OrbStack download and documentation: https://orbstack.dev/download
