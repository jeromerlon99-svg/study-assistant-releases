# Security policy

Study Assistant is a local, private application. Report suspected security or
privacy issues directly to the project owner; do not publish databases, logs,
course media, transcripts, API keys, or screenshots containing private data.

## Security properties

- The Agent listens on loopback and desktop requests use a per-process session
  token.
- Model API keys are memory-only and are cleared on every application launch.
- `runtime-data/` is intentionally excluded from version control.
- Course transcripts and generated notes are sent to the model provider chosen
  by the user when intelligent processing is requested.
- Downloaded transcription and semantic models remain local under
  `runtime-data/models/`.

Before sharing diagnostic material, remove authorization headers, URLs with
tokens, course content, absolute personal paths, and database or model files.
