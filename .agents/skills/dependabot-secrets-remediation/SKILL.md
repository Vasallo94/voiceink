---
name: dependabot-secrets-remediation
description: Remediate Dependabot vulnerabilities and leaked secrets in GitHub repositories, including lockfile patching, history rewriting, and verification. Keywords: dependabot, vulnerability, secret leak, git-filter-repo, uv, pyright, pre-commit.
---
# SKILL: Dependabot + Secrets Remediation in GitHub

## Goal
Close dependency security alerts and remove secret exposure from the repository (including Git history), using this project's standard `uv` workflow.

## When to use it
- GitHub shows Dependabot alerts (especially `high`/`critical`).
- A secret was committed by mistake (for example in `.env`).
- You need reproducible mitigation and verification steps.

## Prerequisites
- `gh` authenticated (`gh auth status`).
- `uv` installed.
- Permission to run `push --force` if history is rewritten.

## Golden rule
If a secret was exposed:
1. **Rotate/revoke the credential first.**
2. Then clean the repository history.

---

## Flow A — Dependabot (vulnerable dependency)

### 1) Identify package and patched version
```bash
token=$(gh auth token)
curl -sS \
  -H "Authorization: Bearer $token" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/Vasallo94/voice2clip/dependabot/alerts \
| jq -r '.[] | [.number, .state, .dependency.package.name, .security_advisory.severity, .security_vulnerability.vulnerable_version_range, (.security_vulnerability.first_patched_version.identifier // "n/a")] | @tsv'
```

### 2) Apply minimal lockfile patch
```bash
uv lock --upgrade-package <package>
uv sync --frozen
```

### 3) Run quality checks
```bash
export PATH="$HOME/.local/bin:$PATH"
uv run pre-commit run --all-files
```

### 4) Commit + push
```bash
git add uv.lock
git commit -m "fix: upgrade <package> to address dependabot alert"
git push origin main
```

### 5) Verify alert closure
```bash
token=$(gh auth token)
curl -sS \
  -H "Authorization: Bearer $token" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/Vasallo94/voice2clip/dependabot/alerts \
| jq -r '.[] | [.number, .state, .dependency.package.name] | @tsv'
```
Expected state: `fixed`.

---

## Flow B — Secret exposed in Git history

### 1) Ensure git exclusion rules
- Keep `.env` ignored in `.gitignore`.
- Keep a public template in `.env.example`.

### 2) Clean history (if already published)
```bash
uvx git-filter-repo --force --invert-paths \
  --path .env \
  --path .gemini/GEMINI.md \
  --path .gemini/agents/debugger.md
```

### 3) Verify no trace remains
```bash
git log --all --name-only --pretty=format: | rg '^(\.env$|\.gemini/)'
```
No output = clean.

### 4) Restore remote and force update
`git-filter-repo` may remove `origin` automatically.
```bash
git remote add origin https://github.com/Vasallo94/voice2clip.git   # if missing
git push --force origin main
```

---

## Final checks
- `git status --short` vacío.
- Target Dependabot alerts in `fixed` state.
- Secrets rotated and working locally.
- README/operational docs reflect current process.

## Common issues
- `pyright not found` en pre-commit:
  - Install: `uv tool install pyright`
  - Persist PATH in zsh:
    ```bash
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
    ```
- `--force-with-lease` rejected after rewrite:
  - Use `git push --force origin main`.

## Expected outcome
Clean repository (working tree + history), closed alerts, and a repeatable remediation process for future incidents.
