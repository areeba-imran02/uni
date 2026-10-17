# API quick reference
All `/api` routes except register/login require `Authorization: Bearer <token>`.

- `GET /health` — service status.
- `POST /api/auth/register` — `{name,email,password}`.
- `POST /api/auth/login` — `{email,password}`.
- `GET /api/auth/me` — current profile.
- `GET /api/projects` — current user's projects.
- `POST /api/projects` — create project.
- `GET /api/projects/{id}` — project and run history.
- `PATCH /api/projects/{id}` — update project fields.
- `DELETE /api/projects/{id}` — delete owned project and its history.
- `POST /api/projects/{id}/run` — execute and persist a workflow.
- `GET /api/runs/{id}` — run result and recorded agent steps.
- `POST /api/uploads` — validate upload (5 MB max; not persisted).
- `GET /docs` — interactive OpenAPI docs.
