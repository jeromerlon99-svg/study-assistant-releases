# Repository layout

| Path | Purpose | Version controlled |
| --- | --- | --- |
| `apps/desktop/` | React UI and Tauri desktop shell | Yes |
| `services/agent/` | FastAPI Agent, storage, retrieval, transcription, notes, and Q&A | Yes |
| `scripts/` | Repeatable checks and packaging helpers | Yes |
| `tests/` | Permanent regression-test source | Yes |
| `docs/` | Architecture, operational notes, and repository policy | Yes |
| `runtime-data/` | User database, course media, models, exports, and logs | No |
| `development-artifacts/` | Disposable test/build reports, caches, and temporary files | No |
| `preview-builds/` | Local portable preview executables | No |
| `output/`, `tmp/` | Local release attachments and temporary work | No |
| `node_modules/` | Restored JavaScript dependencies | No |

The physical working folder may contain both source and ignored local state. A
clean Git checkout contains only the version-controlled rows above; dependencies
and runtime state are restored or created locally.

## Source-of-truth files

- Product version: `VERSION`
- Conda environment: `environment.yml`
- Resolved Windows Python dependencies: `requirements-lock.txt`
- JavaScript dependencies: `pnpm-lock.yaml`
- Rust dependencies: `apps/desktop/src-tauri/Cargo.lock`
- Python dependency ranges: `services/agent/pyproject.toml`
- Runtime configuration example: `.env.example`

Python packages have compatible ranges in `pyproject.toml` and an exact Windows
resolution in `requirements-lock.txt`. Before a release on another platform,
resolve and archive a platform-specific lock from that release environment.
