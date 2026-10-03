# Git Workflow & Collaboration Guidelines

## Project: Multi-Agent AI Document Intelligence System

---

## 1. Branching Strategy

The repository follows a clean trunk-based branch workflow designed for XP and Scrum iterations:

```text
main (Production-ready & Sprint releases)
 │
 ├── feature/<feature-name>     # New capabilities or agent implementations
 ├── fix/<issue-name>           # Bug fixes and edge-case patches
 └── docs/<doc-topic>           # Documentation, specifications, and architecture
```

### Branch Rules
- **`main`**: The primary branch representing tested, verified deliverables. All code on `main` must pass the automated test suite and CI checks.
- **`feature/*`**: Short-lived branches dedicated to specific user stories or sprint backlog items.
- **`fix/*`**: Target branches for correcting test failures or defect reports.
- **`docs/*`**: Non-code changes addressing requirements, architecture, or sprint reports.

---

## 2. Standard Development Lifecycle

Follow these steps for any code contribution:

### Step 1: Create a Topic Branch
```bash
git checkout -b feature/<feature-name>
```
*(e.g., `git checkout -b feature/sprint1-pdf-parser`)*

### Step 2: Implement Code and Accompanying Tests
In accordance with XP practices, develop automated tests alongside functional code.

### Step 3: Verify Locally
Ensure all tests pass before staging:
```bash
pytest -v
```

### Step 4: Stage & Commit Using Conventional Prefixes
```bash
git add .
git commit -m "<prefix>: <imperative summary of change>"
```

### Step 5: Push Branch to Remote
```bash
git push -u origin feature/<feature-name>
```

### Step 6: Create Pull Request & Merge
Open a Pull Request targeting `main`. Ensure GitHub Actions CI passes before merging.

---

## 3. Commit Message Conventions

Commit messages must follow standard conventional commit prefixes:

| Prefix | Usage | Example |
| :--- | :--- | :--- |
| `feat:` | A new user-facing feature or agent capability | `feat: implement docx parser in IngestionAgent` |
| `fix:` | A bug fix or error resolution | `fix: handle empty pdf file without crashing pipeline` |
| `docs:` | Documentation changes only | `docs: define functional requirements in requirements.md` |
| `test:` | Adding, refactoring, or updating tests | `test: add unit tests for timed_agent decorator` |
| `refactor:` | Code restructuring that neither fixes a bug nor adds a feature | `refactor: extract chunking logic into separate service` |
| `chore:` | Build tasks, package updates, or configuration changes | `chore: update requirements.txt with sqlalchemy` |

---

## 4. Integrity Constraints
- **Preserve History:** Never rewrite Git history using `git rebase -i` on shared branches or force-pushing (`--force`) to `main`.
- **Atomic Commits:** Each commit should represent a coherent, reviewable unit of work accompanied by test validation where applicable.
