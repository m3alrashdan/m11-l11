# M10 Frontend (Stub)

This directory holds a stub `Dockerfile` and `package.json` for the Next.js
frontend tier of the M10 stack. The M11 Lab template does **not** ship the
actual Next.js source — only enough scaffolding to define the service shape.

To avoid a build failure on `docker compose up -d`, the `web` service is
gated behind a `frontend` Compose profile, so the default stack-up command
brings up `neo4j` + `weaviate` + `api` only. The M11 Lab's autograder does
not exercise the web tier.

If you want to bring the frontend up alongside the M11 stack, mount your
M10 frontend source into this directory and run
`docker compose --profile frontend up -d`.
