# SocialAdda
This is our BCA final semester project on social media using django created by @Darshil-Solanki and @ManojSalet and currently maintained by @Darshil-Solanki

## Configuration
Settings are read from environment variables (see `SocialAdda/settings.py`):

| Variable | Purpose | Default |
|---|---|---|
| `DJANGO_DEBUG` | Development mode. On unless set to `0`; `0` turns on production settings (secure cookies, HSTS, JSON-only API) | on |
| `DJANGO_SECRET_KEY` | Required when `DJANGO_DEBUG=0`. Development uses a built-in key | none |
| `DJANGO_HTTPS` | Secure cookies and HSTS (only when `DJANGO_DEBUG=0`). Set `0` for plain-HTTP local stacks | `1` |
| `DJANGO_SSL_REDIRECT` / `DJANGO_BEHIND_PROXY` / `DJANGO_HSTS_SECONDS` | Redirect HTTP to HTTPS; trust `X-Forwarded-Proto` from a TLS proxy; HSTS lifetime | `0` / off / `3600` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Comma-separated origins for HTTPS form posts (for example `https://social.example.com`) | none |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated host names | `localhost,127.0.0.1` |
| `EMAIL_HOST` / `EMAIL_PORT` / `EMAIL_USE_TLS` | SMTP server for welcome and reset emails | `smtp.gmail.com` / `587` / on |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | SMTP credentials | empty |
| `DEFAULT_FROM_EMAIL` | Sender address | `SocialAdda Team <noreply@SocialAdda.com>` |
| `REDIS_URL` | Channel layer for chat | `redis://localhost:6379` |
| `CELERY_BROKER_URL` | Background job broker (Redis, database 1) | `REDIS_URL` + `/1` |
| `MEDIA_STORAGE` | `local` (media/ folder) or `s3` (S3 or MinIO bucket) | `local` |
| `AWS_STORAGE_BUCKET_NAME` | Bucket for uploads (required when `MEDIA_STORAGE=s3`) | none |
| `AWS_S3_REGION_NAME` / `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | S3 credentials and region | from the environment |
| `AWS_S3_ENDPOINT_URL` | Only for S3-compatible servers such as MinIO (for example `http://localhost:9000`) | none (AWS) |
| `AWS_S3_CUSTOM_DOMAIN` | Optional CDN or public host for uploaded files | none |
| `EMAIL_BACKEND` | Mail backend; use `django.core.mail.backends.console.EmailBackend` to print emails | SMTP |
| `FRONTEND_URL` | Base URL of the frontend, used in password-reset links | `http://localhost:3000` |
| `POSTGRES_DB` (+ `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`) | Use PostgreSQL. Without `POSTGRES_DB` the app uses SQLite | SQLite |

Local run (development mode):
```
pip install -r requirements-dev.txt
cp .env.example .env          # optional: the defaults already run in development mode
python manage.py migrate
python manage.py runserver
```

Settings come from environment variables. `SocialAdda/settings.py` loads a `.env` file from the project root with
python-dotenv. The file is git-ignored, and variables already set in the shell or the platform take precedence.
`.env.example` starts the project in development mode (`DJANGO_DEBUG=1`, SQLite, console email). Production must set
its values in the environment or the platform's secret store, not in a committed file.

Frontend: `cp frontend/.env.example frontend/.env.local`, then `npm run dev` in `frontend/`.

Run `python manage.py migrate` after every pull. A database that has not been migrated makes the API return server errors, which the dashboard shows as an error message.

REST API (JWT auth, class-based DRF views). Interactive docs at `/api/docs/`, OpenAPI schema at `/api/schema/`.

| Area | Endpoints |
|---|---|
| Auth | `POST auth/register/`, `POST auth/token/`, `POST auth/token/refresh/`, `POST auth/logout/` (revokes the refresh token), `POST auth/password-reset/`, `POST auth/password-reset/confirm/`, `GET/PATCH me/` |
| Posts | `GET/POST posts/`, `GET/PATCH/DELETE posts/{id}/`, `POST/DELETE posts/{id}/like/`, `POST/DELETE posts/{id}/bookmark/`, `GET/POST posts/{id}/comments/` |
| Feeds | `GET feed/following/`, `GET saved/` |
| Notifications | `GET notifications/`, `GET notifications/unread-count/`, `POST notifications/read/` |
| Users | `GET users/?q=`, `GET users/suggestions/`, `GET users/{username}/`, `POST/DELETE users/{username}/follow/` |
| Chat | `GET conversations/`, `GET/POST conversations/{username}/messages/`, `POST conversations/{username}/read/` |

Lists use cursor pagination (`next` / `previous`) for posts, comments and messages. Live messages use the WebSocket at `/ws/{user_id}/` with the access token as the `socialadda` subprotocol (`new WebSocket(url, ['socialadda', token])`).

Frontend (Next.js + TypeScript): see `frontend/README.md`. Start the backend, then run `npm run dev` in `frontend/` and open http://localhost:3000.

Live features:
- Notifications (likes, comments, follows) are stored, pushed over `ws/notifications/` (token as the `socialadda` subprotocol), and listed at `/api/v1/notifications/`.
- Chat sends typing indicators and read receipts over `ws/<user id>/` (token as the `socialadda` subprotocol) (`{"type": "typing"}` and `{"type": "read"}`).
- Post images get a WebP thumbnail from the Celery worker; the feed uses it when ready.

Background worker (sends emails, pushes notifications, makes thumbnails; needs Redis running):
```
celery -A SocialAdda worker -l info
```

Object storage: the default keeps uploads in `media/`. To use S3 or MinIO set `MEDIA_STORAGE=s3` with the variables above. Uploads are then public-read, so the bucket needs a read policy (or a CDN in front of it).

Demo data: `python manage.py seed_demo --users 12` creates demo users (password `demo-pass-123`) with follows, posts, likes and comments. Load test: see `docs/loadtest.md` and `loadtest/`.


Run tests:
```
DJANGO_SECRET_KEY=test-only-key python manage.py test
```

This project has several dependencies like redis you can easily download redis from there official website [Redis](https://redis.io/downloads). Runtime requirements are in `requirements.txt`. `requirements-dev.txt` adds the test and load-test tools:
```
pip install -r requirements-dev.txt
```

Dependency audits: `pip-audit -r requirements.txt` and `npm audit` in `frontend/`. CI runs both.

This project is live over [here](https://socialadda.darshilsolanki.com)
