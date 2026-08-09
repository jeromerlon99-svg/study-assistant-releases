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
