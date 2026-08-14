# Upstream Tracking

GoreeVault begins from Vaultwarden and should keep a clean upstream relationship during the compatibility phase.

Recommended remotes:

```bash
git remote -v
git remote add upstream https://github.com/dani-garcia/vaultwarden.git
```

Recommended update workflow:

```bash
git fetch upstream
# review upstream changes first
git log --oneline --decorate --graph main..upstream/main
# merge/rebase only through a reviewed branch/PR
```

Never automatically deploy an upstream merge to production. Upstream merges must pass GoreeVault CI, compatibility tests and a development deployment first.
