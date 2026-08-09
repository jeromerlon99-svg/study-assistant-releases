# Development guide

Study Assistant is currently a private, proprietary project. This guide defines
the local workflow so future changes remain reproducible and reviewable.

## Repository boundaries

- Product source lives in `apps/`, `services/`, and `scripts/`.
- Permanent automated tests live in `tests/` and belong in version control.
- User data, downloaded models, media, databases, and exports live in
  `runtime-data/` and must never be committed.
- Disposable test reports, caches, screenshots, and packaging work files live
  in `development-artifacts/` and can be removed as a unit.
- Portable preview executables live in `preview-builds/` and are not source.

## Environment

Create or update the shared environment from the repository root:

```powershell
conda env update --file environment.yml --prune
conda activate study-assistant
python -m pip install -c requirements-lock.txt -e "./services/agent[dev,build]"
pnpm install --frozen-lockfile
```

Windows also requires the Rust MSVC toolchain, Visual C++ Build Tools, a Windows
SDK, and the Edge WebView2 runtime.

`requirements-lock.txt` records the exact Python resolution used by the current
Windows development/release environment. Update it only as part of a reviewed
dependency upgrade.

## Required checks

Run the unified check before accepting a change:

```powershell
pnpm check
```

The command checks version consistency, Python dependencies, Ruff, pytest, the
frontend production build, Rust formatting, and Clippy. Test reports and Rust
build caches are written to `development-artifacts/`; Vite writes its required,
ignored frontend bundle to `apps/desktop/dist/`.

## Versioning and release builds

`VERSION` is the source of truth. Update all application manifests together and
run `pnpm check:version`. A normal quality check does not generate an installer.
Only use `pnpm release:build` when a release package is explicitly required.

Never commit API keys, `runtime-data/`, generated executables, model weights, or
personal course material. Do not rewrite or delete user data while preparing a
source change.
