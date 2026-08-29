# PostgreSQL + Themes upgrade

## Local testing
If DATABASE_URL is not set, the app automatically uses local SQLite.

## Render production database
1. Create a PostgreSQL database in Render.
2. Copy its Internal Database URL into the Web Service environment variable `DATABASE_URL`.
3. Redeploy. The app automatically creates the required tables.
4. Keep Build Command: `pip install -r requirements.txt`
5. Keep Start Command: `gunicorn app:app`

The SQLite file remains only as a local fallback.

## Themes
The UI now includes theme presets: Aurora, Ocean, Sunset, and Midnight. The selected theme is saved in the browser.
