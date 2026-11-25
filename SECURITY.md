# Security policy

Study Assistant runs its Agent locally. Report suspected security or
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

The Agent omits HTTP access logs because event-stream URLs contain a local
session token. Before sharing older logs or other diagnostic material, remove
authorization headers, `/events?token=…` URLs, course content, absolute personal
paths, and database or model files.
