# Contributing to AIO

Welcome! This guide explains how to contribute safely and effectively to AIO.

## Setup

```bash
# Clone and install
git clone https://github.com/renatobardi/aio.git
cd aio
pip install -e ".[dev]"
pip install -e ".[enrich]"

# Configure hapai (code safety guardrails)
hapai install
hapai status
```

## Workflow

### 1. Create Feature Branch

```bash
git checkout -b feat/your-feature-name
# or: fix/bug-name, docs/update-readme, refactor/module-name, etc.
```

**Branch naming** (enforced by hapai):
- `feat/` — new features
- `fix/` — bug fixes
- `docs/` — documentation
- `refactor/` — code improvements
- `test/` — test additions
- `chore/` — maintenance
- `perf/` — performance
- `style/` — formatting
- `ci/` — CI/CD changes
- `build/` — build system
- `release/` — releases
- `hotfix/` — urgent fixes

### 2. Make Changes

```bash
# Edit code, add tests, commit frequently
git add src/my_file.py tests/test_my_file.py
git commit -m "feat: add image caching for Pollinations API"
```

**Commit message rules** (enforced by hapai):
- ✅ Start with type: `feat:`, `fix:`, `docs:`, etc.
- ✅ Use lowercase, present tense
- ❌ NO `Co-Authored-By: Claude ...` trailers
- ❌ NO mentions of AI tools in commit messages

### 3. Validate Locally

Before pushing, run the full validation suite:

```bash
# Lint + format
ruff check src/ tests/ && ruff format src/ tests/

# Type checking
mypy src/aio/

# Tests + coverage
pytest tests/ -v --cov=src/aio --cov-fail-under=20

# Manual verification
aio build tests/fixtures/sample.md -o /tmp/test.html
```

### 4. Push & Create PR

```bash
git push origin feat/your-feature-name
gh pr create --title "feat: brief description" --body "..."
```

**Hapai will enforce:**
- ❌ No pushing to `main` or `master` directly
- ❌ No edits to `.env`, `.github/workflows/`, or lockfiles
- ❌ No destructive commands

If hapai blocks you, the error message explains why — fix it and try again.

### 5. Code Review & Merge

- Respond to review feedback
- Once approved, squash and merge to `main`
- Delete feature branch (local and remote)

```bash
git branch -d feat/your-feature-name
git push origin --delete feat/your-feature-name
```

## Guardrails (Hapai)

Hapai automatically protects the repo. Key rules:

| Rule | Why | Blocked Action |
|------|-----|---|
| No direct commits to `main` | Enforces code review | `git commit` on main |
| Branch naming convention | Maintains order | `git checkout -b my-feature` |
| No `.env` edits | Prevents secrets leaks | Edits to `.env*` files |
| No lockfile edits | Prevents dependency issues | Direct edits to `package-lock.json`, `requirements.lock`, etc. |
| No destructive commands | Prevents data loss | `git reset --hard`, `rm -rf`, `DROP TABLE` |

**If blocked:** Read hapai's error message, fix the issue, then retry.

## Testing

```bash
# Unit tests (fast, isolated)
pytest tests/unit/ -v

# Integration tests (full pipeline)
pytest tests/integration/ -v

# Single test
pytest tests/unit/test_parser.py::test_parse_frontmatter -v

# Coverage
pytest --cov=src/aio --cov-report=html
open htmlcov/index.html
```

**Coverage gate:** ≥20% (CI requirement), target 80%

## Documentation

Update these files when relevant:
- `README.md` — user-facing features
- `CLAUDE.md` — architecture, module map, patterns
- `docs/` — guides, troubleshooting, specs
- `.specify/memory/constitution.md` — architectural principles

## Specs & Planning

Design docs live in `specs/main/`:
- `plan.md` — M0–M4 roadmap
- `research.md` — tech decisions
- `data-model.md` — entities & relationships
- `quickstart.md` — dev recipes
- `contracts/` — CLI, API contracts

Read these before major refactors.

## Questions?

- Architecture: Read `CLAUDE.md` module map
- Specs: Check `specs/main/plan.md`
- Git/hapai issues: See README Contributing section
- Code style: Run `ruff format`

---

**Remember:** Hapai is your friend. It protects the repo automatically — just follow branch naming and commit message rules, and you're good.
