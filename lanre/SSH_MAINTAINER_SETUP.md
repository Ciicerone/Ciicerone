# SSH-Based Git Authentication for Ciicerone Maintainers

This guide enables **secure, passwordless git operations** from a **single trusted device** per maintainer using SSH keys with Ed25519 encryption and SSH agent forwarding.

---

## Prerequisites

- **One trusted device** (laptop/workstation) per maintainer
- **GitHub account** with 2FA enabled
- **OpenSSH 8.2+** (for Ed25519 support)
- **Git 2.34+** (for `git config --global` credential helpers)

---

## 1. Generate Dedicated SSH Key (Per Maintainer)

Run **once** on your trusted device:

```bash
# Generate Ed25519 key with maintainer-specific comment
ssh-keygen -t ed25519 -C "ciicerone-maintainer-<GITHUB_HANDLE>-$(date +%Y%m%d)" \
  -f ~/.ssh/id_ed25519_ciicerone

# Example for @laradipupo:
ssh-keygen -t ed25519 -C "ciicerone-maintainer-laradipupo-20260711" \
  -f ~/.ssh/id_ed25519_ciicerone
```

**Output:**
```
Generating public/private ed25519 key pair.
Enter passphrase (empty for no passphrase): [USE STRONG PASSPHRASE]
Enter same passphrase again: [CONFIRM]
Your identification has been saved in /home/user/.ssh/id_ed25519_ciicerone
Your public key has been saved in /home/user/.ssh/id_ed25519_ciicerone.pub
```

> **Security**: Always use a passphrase. The SSH agent will cache it.

---

## 2. Add Key to SSH Agent (Persistent)

```bash
# Start SSH agent if not running
eval "$(ssh-agent -s)"

# Add key with 8-hour timeout (re-prompts passphrase daily)
ssh-add -t 8h ~/.ssh/id_ed25519_ciicerone

# Verify
ssh-add -l
```

**Persist across reboots** (macOS):
```bash
# Add to ~/.ssh/config (see step 3) - UseKeychain yes handles this
```

**Persist across reboots** (Linux):
```bash
# Add to ~/.bashrc or ~/.zshrc
if [ -z "$SSH_AUTH_SOCK" ]; then
  eval "$(ssh-agent -s)" > /dev/null
  ssh-add -t 8h ~/.ssh/id_ed25519_ciicerone 2>/dev/null || true
fi
```

---

## 3. SSH Config for Ciicerone Repos

Edit `~/.ssh/config`:

```ssh
# === Ciicerone Maintainer Config ===
Host github-ciicerone
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_ciicerone
    IdentitiesOnly yes
    AddKeysToAgent yes
    UseKeychain yes              # macOS: stores passphrase in Keychain
    ForwardAgent no              # Disable forwarding (security)
    ServerAliveInterval 60
    ServerAliveCountMax 2

# Optional: Separate config for upstream vs fork
Host github-ciicerone-upstream
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_ciicerone
    IdentitiesOnly yes

Host github-ciicerone-fork
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_ciicerone
    IdentitiesOnly yes
```

> **Why `IdentitiesOnly yes`**: Prevents SSH from trying other keys (security).

---

## 4. Add Public Key to GitHub

```bash
# Copy public key
cat ~/.ssh/id_ed25519_ciicerone.pub | pbcopy  # macOS
# cat ~/.ssh/id_ed25519_ciicerone.pub | xclip -sel clip  # Linux
```

1. Go to **GitHub → Settings → SSH and GPG keys → New SSH key**
2. **Title**: `Ciicerone Maintainer - <GITHUB_HANDLE> - <DEVICE_NAME>`
3. **Key type**: **Authentication Key** (for git operations)
4. **Paste** the public key
5. **Save** → Confirm with 2FA

---

## 5. Clone Using SSH (Not HTTPS)

```bash
# Clone YOUR fork (replace <GITHUB_HANDLE>)
git clone git@github-ciicerone-fork:<GITHUB_HANDLE>/Ciicerone.git
cd Ciicerone

# Add upstream remote (Ciicerone org)
git remote add upstream git@github-ciicerone-upstream:Ciicerone/Ciicerone.git

# Verify
git remote -v
```

**Expected output:**
```
origin    git@github-ciicerone-fork:laradipupo/Ciicerone.git (fetch)
origin    git@github-ciicerone-fork:laradipupo/Ciicerone.git (push)
upstream  git@github-ciicerone-upstream:Ciicerone/Ciicerone.git (fetch)
upstream  git@github-ciicerone-upstream:Ciicerone/Ciicerone.git (push)
```

---

## 6. Configure Git for Maintainer Identity

```bash
# Inside the repo
git config user.name "<GITHUB_HANDLE>"
git config user.email "<GITHUB_HANDLE>@users.noreply.github.com"

# Example for @laradipupo:
git config user.name "laradipupo"
git config user.email "laradipupo@users.noreply.github.com"

# Optional: Sign commits with SSH key (Git 2.34+)
git config gpg.format ssh
git config user.signingkey ~/.ssh/id_ed25519_ciicerone.pub
git config commit.gpgsign true
```

---

## 7. Daily Workflow (Secure)

```bash
# Morning: unlock key (once per 8 hours)
ssh-add -t 8h ~/.ssh/id_ed25519_ciicerone

# Sync upstream
git fetch upstream
git checkout main
git merge upstream/main --ff-only

# Create feature branch
git checkout -b feat/my-task

# Work, commit (auto-signed if configured)
git add .
git commit -m "feat: description"

# Push to YOUR fork
git push origin feat/my-task

# Create PR via CLI (routes to correct maintainer fork)
gh pr create --base main --head feat/my-task --repo Ciicerone/Ciicerone
```

---

## 8. Security Hardening

### Revoke Compromised Key
```bash
# 1. Remove from GitHub: Settings → SSH keys → Delete
# 2. Generate new key (step 1)
# 3. Add new key to GitHub (step 4)
# 3. Update ~/.ssh/config if filename changed
```

### Audit Active Keys
```bash
# List keys in agent
ssh-add -l

# Test GitHub auth
ssh -T git@github-ciicerone-upstream
# Should show: "Hi <HANDLE>! You've successfully authenticated..."
```

### Device Loss Protocol
If trusted device is lost/stolen:
1. **Immediately** revoke key on GitHub (Settings → SSH keys → Delete)
2. Generate new key on replacement device
3. Notify the core team for audit log review

---

## 9. Troubleshooting

| Issue | Fix |
|-------|-----|
| `Permission denied (publickey)` | Check `ssh-add -l` shows key; verify `~/.ssh/config` Host matches remote |
| `Agent admitted failure to sign` | `ssh-add ~/.ssh/id_ed25519_ciicerone` |
| `Could not open a connection to your authentication agent` | `eval "$(ssh-agent -s)"` then `ssh-add` |
| Multiple GitHub accounts | Use separate `Host` entries in `~/.ssh/config` with different `IdentityFile` |
| Passphrase prompt every time | macOS: `UseKeychain yes` in config; Linux: ensure `ssh-agent` persists in shell rc |

---

## 10. Maintainer Quick Reference Card

| Maintainer | Fork Remote | Upstream Remote | SSH Config Host (fork) | SSH Config Host (upstream) |
|------------|-------------|-----------------|------------------------|----------------------------|
| @laradipupo | `origin` | `upstream` | `github-ciicerone-fork` | `github-ciicerone-upstream` |
| @noblenabeela360 | `origin` | `upstream` | `github-ciicerone-fork` | `github-ciicerone-upstream` |
| @onojad | `origin` | `upstream` | `github-ciicerone-fork` | `github-ciicerone-upstream` |
| @ajiboyshokunbi | `origin` | `upstream` | `github-ciicerone-fork` | `github-ciicerone-upstream` |
| @hrlanreshittu | `origin` | `upstream` | `github-ciicerone-fork` | `github-ciicerone-upstream` |
| @Okino007 | `origin` | `upstream` | `github-ciicerone-fork` | `github-ciicerone-upstream` |
| @AdebolaH | `origin` | `upstream` | `github-ciicerone-fork` | `github-ciicerone-upstream` |
| @BlessingOUdoh-ui | `origin` | `upstream` | `github-ciicerone-fork` | `github-ciicerone-upstream` |

**All maintainers use the same SSH config hosts** — only the `git clone` URL changes (fork username).

---

## 11. CI/CD Integration (Optional)

For GitHub Actions that need to push (e.g., dependabot, release automation):

```yaml
# .github/workflows/auto-merge.yml
jobs:
  auto-merge:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ssh-key: ${{ secrets.MAINTAINER_SSH_KEY }}  # Org-level secret
          persist-credentials: true
```

> **Note**: CI uses a separate machine user key, not maintainer personal keys.

---

## Summary Checklist

- [ ] Generate Ed25519 key with passphrase
- [ ] Add to SSH agent with timeout
- [ ] Configure `~/.ssh/config` with `github-ciicerone-*` hosts
- [ ] Add public key to GitHub account
- [ ] Clone fork via SSH (`git@github-ciicerone-fork:...`)
- [ ] Add upstream remote via SSH (`git@github-ciicerone-upstream:...`)
- [ ] Set git user.name/email per repo
- [ ] Enable commit signing (optional)
- [ ] Test: `ssh -T git@github-ciicerone-upstream`
- [ ] Daily: `ssh-add -t 8h ~/.ssh/id_ed25519_ciicerone`

**One device. One key. Zero passwords in git operations.**