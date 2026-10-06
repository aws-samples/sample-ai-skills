# Framework Detection Reference

Shared detection logic for documentation skills. Referenced by ai-diataxis for two jobs: detecting the published docs root when `docs_path` is absent, and finding the project's **placement convention** — where a new page goes once the root is known. The two are separate reads and the second is not conditional on the first: a project can carry `docs_path` in `.ai-skills.toml` and still record its placement convention only in prose.

## Detection Priority

1. **CLAUDE.md Context** (highest signal) — Check for doc paths, the placement convention (which directory a new page goes in, and whether the tree is partitioned by anything above or below the four modes), framework name, conventions, guidance file pointers. Read the file **by path** — `dirname(docs_path)/CLAUDE.md` and the project root's — rather than relying on it being in ambient context. In Kiro, read `.kiro/steering/*.md` as well: that runtime loads `.kiro/steering/`, not `CLAUDE.md`, so a rule assuming ambient presence resolves nothing there.
2. **Framework Detection** (filesystem probing) — Match config files to frameworks
3. **Heuristic Discovery** (fallback) — Look for common doc directories

## Framework Detection Table

| Config file | Framework | Typical docs location |
|---|---|---|
| `docusaurus.config.{ts,js}` | Docusaurus | `docs/` or `website/docs/` |
| `mkdocs.yml` | MkDocs | `docs/` |
| `conf.py` + `index.rst` | Sphinx | `source/` or `docs/source/` |
| `.vitepress/config.{ts,js}` | VitePress | parent of `.vitepress/` |
| `book.toml` | mdBook | `src/` |
| `_config.yml` + jekyll theme | Jekyll | `docs/` |

## Heuristic Fallback

If no framework detected:
- Look for `docs/`, `documentation/`, `wiki/` directories
- Find concentrations of `.md` files
- Check for `CONTRIBUTING.md`, `ARCHITECTURE.md`, `DEVELOPMENT.md`
- **Ask the user** where docs should go
