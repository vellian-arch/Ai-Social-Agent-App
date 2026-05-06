# AI Social Agent

AI Social Agent is a subscription-gated social commerce command center built with Python.

It combines:

- A Streamlit dashboard for operators
- A FastAPI backend for integrations and webhooks
- AI-assisted replies and follow-ups
- Monthly subscription billing
- Media upload and content management
- Platform connection flows for social channels

## What It Does

- Manage conversations across connected platforms
- Upload media from local files and store it through the backend
- Connect social platforms through OAuth where supported
- Generate AI-assisted replies and follow-up actions
- Gate workspace access behind an active monthly subscription

## Sponsorship

Social Ai Agent is a startup app built to help small businesses connect their social platforms, manage conversations, use AI replies, and turn social engagement into sales from one workspace.

Sponsorship helps cover the startup costs needed to keep the app live and improving, including hosting, database services, AI/API usage, payment processing setup, security, testing, and ongoing development.

Any amount helps keep the project moving while we build a reliable product for real business users.

## Repository Layout

```text
ai-social-agent/
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- core/
|   |   |-- integrations/
|   |   |-- legacy/
|   |   |-- services/
|   |   |-- ui/
|   |   `-- workers/
|   |-- scripts/
|   |-- dashboard.py          # Streamlit compatibility wrapper
|   |-- main.py               # FastAPI compatibility wrapper
|   |-- database.py           # Database compatibility wrapper
|   |-- requirements.txt
|   `-- start_saintvellian.bat
|-- render.yaml
|-- streamlit_app.py
|-- requirements.txt
|-- uploads/
`-- README.md
```

## Local Setup

1. Create and activate a virtual environment.
2. Install backend dependencies:

```powershell
pip install -r backend/requirements.txt
```

3. Copy the example environment file:

```powershell
Copy-Item backend/.env.example backend/.env
```

4. Fill in your real API keys, database URL, and callback URLs in `backend/.env`.

5. Start the backend API:

```powershell
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

6. Start the dashboard in a second terminal:

```powershell
cd backend
streamlit run dashboard.py
```

You can also run the dashboard entrypoint from the repository root:

```powershell
streamlit run streamlit_app.py
```

## Environment Variables

The app reads configuration from `backend/.env`.

Common values include:

- `DATABASE_URL`
- `BACKEND_PUBLIC_URL`
- `FRONTEND_APP_URL`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `META_APP_ID`
- `META_APP_SECRET`
- `META_REDIRECT_URI`
- `TIKTOK_CLIENT_KEY`
- `TIKTOK_CLIENT_SECRET`
- `TIKTOK_REDIRECT_URI`
- `PAYSTACK_PUBLIC_KEY`
- `PAYSTACK_SECRET_KEY`
- `PAYSTACK_ENV`
- `PAYPAL_CLIENT_ID`
- `PAYPAL_CLIENT_SECRET`
- `PAYPAL_ENV`
- `PAYPAL_ANY_AMOUNT_URL`
- `DODO_PAYMENTS_API_KEY`
- `DODO_ENV`
- `GEMINI_API_KEY`
- `SMTP_HOST`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`

## Deployment

### Render

The repository includes [render.yaml](render.yaml) for the backend service.

### Streamlit Community Cloud

Use [streamlit_app.py](streamlit_app.py) as the app entrypoint.

The root [requirements.txt](requirements.txt) points Streamlit Cloud at the backend requirements file.

For production deployments, use:

```env
API_BASE_URL=https://your-render-service.onrender.com
BACKEND_PUBLIC_URL=https://your-render-service.onrender.com
FRONTEND_APP_URL=https://socialaiagent.streamlit.app
PAYSTACK_CALLBACK_URL=https://socialaiagent.streamlit.app
PAYPAL_RETURN_URL=https://socialaiagent.streamlit.app
PAYPAL_CANCEL_URL=https://socialaiagent.streamlit.app
PAYPAL_ANY_AMOUNT_URL=https://www.paypal.com/donate/?hosted_button_id=YOUR_BUTTON_ID
PUBLIC_PAYPAL_PAYMENT_URL=https://ai-social-agent-app.onrender.com/support/paypal
DODO_RETURN_URL=https://socialaiagent.streamlit.app
```

## Security Notes

- Keep `.env` files out of version control.
- Do not commit OAuth client secrets, payment keys, or database passwords.
- Local database files and upload artifacts are ignored by `.gitignore`.

## Notes

- The main FastAPI app lives at [backend/app/api/main.py](backend/app/api/main.py).
- The main dashboard lives at [backend/app/ui/dashboard.py](backend/app/ui/dashboard.py).
- The AI layer has a fallback path so the app remains usable if the model key is unavailable.
- Monthly subscription billing is enforced before users can access the workspace.
- The platform connection flows depend on the OAuth credentials and redirect URLs you register with each provider.
