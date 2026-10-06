# Northstar Login

A small Flask login app with PostgreSQL persistence, password hashing, CSRF protection, and Docker Compose.

## Run locally with Docker Compose

1. Copy `.env.example` to `.env`.
2. For a public deployment, replace `POSTGRES_PASSWORD` and `SECRET_KEY` with unique, strong values. Set `SESSION_COOKIE_SECURE=true` when served over HTTPS.
3. Start the app:

   ```sh
   docker compose up --build
   ```

4. Open <http://localhost:8000> and create an account.

The app listens on port 8000. PostgreSQL data is persisted in the `postgres_data` named volume. The database schema is initialized on the first start; if the database volume already exists, the init script will not be rerun.

To stop the services, run `docker compose down`. To also delete the local database and its accounts, run `docker compose down -v`.

## Configuration

Compose reads variables from `.env`:

| Variable | Purpose |
| --- | --- |
| `POSTGRES_HOST` | Database host (set to `db` in Compose) |
| `POSTGRES_PORT` | Database port |
| `POSTGRES_DB` | Database name |
| `POSTGRES_USER` | Database username |
| `POSTGRES_PASSWORD` | Database password |
| `SECRET_KEY` | Flask session signing key |
| `SESSION_COOKIE_SECURE` | Set `true` when HTTPS is enabled |

The values in `.env.example` are for local development only. Do not use them for a public deployment. Use HTTPS and a secrets manager for production credentials.

## Routes

- `/register` creates an account.
- `/login` authenticates with email and password.
- `/dashboard` requires an authenticated session.
- `POST /logout` ends the session.
