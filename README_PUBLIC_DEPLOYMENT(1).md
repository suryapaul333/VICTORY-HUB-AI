# AI Student Performance System - Public Deployment Build

This build is prepared for public demo/testing on Render.

## Render
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Environment variables recommended:
  - `SECRET_KEY` = a long random secret
  - `ADMIN_EMAIL` = email address allowed to open `/admin`
- Optional email variables: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `FROM_EMAIL`

## Health check
`/health` returns JSON when the service is running.

## Important database note
This version keeps SQLite for simplicity and adds WAL/busy-timeout protection. For a high-traffic production service with many simultaneous writes, migrate to PostgreSQL and use persistent storage. Render Free services do not provide persistent disks, so SQLite data should not be treated as durable production storage across redeploys/restarts.

## Public access
Anyone with the Render URL can open the site and create an account. Authentication is still required for student data and prediction pages.
