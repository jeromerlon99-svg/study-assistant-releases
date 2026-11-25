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

## FFmpeg and FFprobe command-line programs

The Windows installer includes the separate `ffmpeg.exe` and `ffprobe.exe`
programs from the BtbN FFmpeg Windows x64 LGPL 8.1 static build. Study Assistant
invokes these programs as separate processes for public-course media inspection
and audio extraction; it does not link against FFmpeg libraries.

- Upstream project: [`FFmpeg`](https://ffmpeg.org/)
- Build release and asset: [`autobuild-2026-11-24-12-41`](https://github.com/FFmpeg-Builds/FFmpeg-Builds/releases/tag/autobuild-2026-11-24-12-41),
  `ffmpeg-n8.1.3-41-ga8029b6528-win64-lgpl-8.1.zip`
- Archive SHA-256: `2201df4d6cbdcbbda9e612645605735821bb4cd0b120a9683f970c4c4e2de8e4`
- Corresponding upstream FFmpeg revision: [`a8029b6528`](https://github.com/FFmpeg/FFmpeg/tree/a8029b6528).
  The release tag also identifies the [build recipes](https://github.com/FFmpeg-Builds/FFmpeg-Builds/tree/autobuild-2026-11-24-12-41).
- License: GNU Lesser General Public License as supplied in the build archive

New builds include the archive's license and the actual configure line in
`ffmpeg-build.txt`. The bundled executables are unmodified.

The previously distributed August 2026 installer uses
`n8.1.2-34-g9b6c8969e0-20260809`, whose
[upstream FFmpeg revision is `9b6c8969e0`](https://github.com/FFmpeg/FFmpeg/tree/9b6c8969e05b4f0b29f0f85cd501be6b3e582e6b).
Its input archive SHA-256 is
`9e7ba6e147252b33458786a3c1c2c9b337d21da1ad53f5d98b1e98d9711e1a5b`.

## PyAV and its native libraries

The Python sidecar uses [PyAV 18.0.0](https://pypi.org/project/av/18.0.0/),
licensed under BSD-3-Clause, to decode audio for faster-whisper. Its Windows
wheel ships native libraries, including a separate build of FFmpeg 8.1.2.
See the [PyAV source and build scripts](https://github.com/PyAV-Org/PyAV/tree/v18.0.0)
and the [FFmpeg 8.1.2 source](https://github.com/FFmpeg/FFmpeg/tree/n8.1.2).
New builds include the PyAV license and `PyAV-build.txt`, which records the
wheel's DLL inventory and the FFmpeg libraries' reported version, license, and
configuration. The native libraries retain their own licenses.
