# Third-party notices

Study Assistant 0.1.7 uses third-party software and can download third-party
model artifacts. The source repository does not store downloaded model weights.

## Software dependencies

JavaScript dependency identities and resolved versions are recorded in
`pnpm-lock.yaml`; Rust dependency identities and resolved versions are recorded
in `apps/desktop/src-tauri/Cargo.lock`; Python dependency declarations are
recorded in `services/agent/pyproject.toml`. Each dependency remains subject to
the license and notices published by its copyright holder. Those licenses are
not replaced by the project-level proprietary license.

## multilingual-e5-small

- Model: [`intfloat/multilingual-e5-small`](https://huggingface.co/intfloat/multilingual-e5-small)
- Model license: MIT
- Local use: multilingual semantic retrieval, 384-dimensional embeddings
- ONNX conversion: [`Xenova/multilingual-e5-small`](https://huggingface.co/Xenova/multilingual-e5-small)
- Pinned artifact revision: `761b726dd34fb83930e26aab4e9ac3899aa1fa78`
- Downloaded weight: `onnx/model_int8.onnx`
- Expected SHA-256: `4d24e2bc01a447951524466ef533e52944bf48509e6552810bcee1a2711cb02c`

The Xenova repository states that it contains ONNX weights converted from the original intfloat model. Study Assistant preserves the original model identity in its local manifest and verifies the pinned weight before loading it.

## faster-whisper models

When a course has no readable subtitles, the user may select a compatible
faster-whisper model for local transcription. Model artifacts are downloaded to
`runtime-data/models/faster-whisper/` on demand and retain the license and usage
terms published with the selected model.

## FFmpeg 8.1

The Windows installer includes the separate `ffmpeg.exe` and `ffprobe.exe`
programs from the BtbN FFmpeg Windows x64 LGPL 8.1 static build. Study Assistant
invokes these programs as separate processes for public-course media inspection
and audio extraction; it does not link against FFmpeg libraries.

- Upstream project: [`FFmpeg`](https://ffmpeg.org/)
- Windows build project: [`BtbN/FFmpeg-Builds`](https://github.com/BtbN/FFmpeg-Builds)
- Build asset: `ffmpeg-n8.1-latest-win64-lgpl-8.1.zip`
- Verified archive SHA-256: `9e7ba6e147252b33458786a3c1c2c9b337d21da1ad53f5d98b1e98d9711e1a5b`
- License: GNU Lesser General Public License as supplied in the build archive

The installer includes the build archive's `LICENSE.txt`. Corresponding FFmpeg
source and reproducible build scripts are available from the upstream and build
project links above. The bundled executables are unmodified.
