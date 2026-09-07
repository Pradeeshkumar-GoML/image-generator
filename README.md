# AI Matic — Personalized Content Generation

Production-grade FastAPI backend and Vite + React frontend for **text-to-image** and **text-to-video** generation with a provider-agnostic factory architecture.

---

## Features

- **Text-to-Image Generation**: `POST /text-to-image` (and `/api/content/text-to-image`) generates PNG images from prompts.
- **Text-to-Video Generation**: `POST /text-to-video` (and `/api/content/text-to-video`) generates MP4 videos from prompts.
- **Modern Web Frontend**: Fast, responsive React 19 + TypeScript + Vite UI with instant media preview, toast notifications, prompt presets, and session gallery.
- **Factory Architecture**: Switch AI providers cleanly via environment configuration (`.env`).
- **Clean Architecture**: Separation of concerns (`API` → `Service` → `Factory` → `Adapter` → `External API`).
- **Health Probes & Diagnostics**: Liveness (`/health`, `/api/health`) and readiness checks with provider status reporting.
- **Dockerized & Cloud Ready**: Production `Dockerfile`, AWS Lambda ASGI handler (`Mangum`), EC2 CloudFormation templates, and CI/CD workflows.
- **Interactive Swagger Docs**: Available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Supported Providers

### Text-to-Image (`TTI_MODEL` or `ACTIVE_TTI_PROVIDER`)

| Value | Provider | Adapter Status | Notes |
|---|---|---|---|
| `openai` | OpenAI DALL-E 3 / GPT-Image | **Active (Default)** | Requires `OPENAI_API_KEY` |
| `gemini` | Google Gemini / Imagen | **Active** | Requires `GOOGLE_API_KEY` |
| `titan` | Amazon Titan Image Generator v2 | **Active** | AWS Titan Image |

### Text-to-Video (`TTV_MODEL` or `ACTIVE_TTV_PROVIDER`)

| Value | Provider | Adapter Status | Notes |
|---|---|---|---|
| `sora` | OpenAI Sora | **Active** | Requires `OPENAI_API_KEY` |
| `veo` | Google Veo | **Active** | Requires `GOOGLE_API_KEY` |
| `nova_reel` | AWS Nova Reel | **Active** | AWS Video Generation |

---

## Quick Start

### 1. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your credentials and active provider selections
```

Example `.env` settings:
```env
TTI_MODEL=openai
TTV_MODEL=sora

OPENAI_API_KEY="your_openai_api_key"
OPENAI_IMAGE_MODEL=dall-e-3
```

### 2. Run the Backend (FastAPI)

```bash
# Setup Python virtual environment
python -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Probe: [http://localhost:8000/health](http://localhost:8000/health)

### 3. Run the Frontend (React + Vite)

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5174](http://localhost:5174) in your browser. The Vite development server automatically proxies API requests to `http://localhost:8000`.

---

## Switching Providers

Change environment variables in `.env` without modifying any application code:

```env
TTI_MODEL=openai
TTV_MODEL=sora
```

Restart the backend server after updating `.env`.

---

## API Usage Examples

### Text-to-Image
```bash
curl -X POST http://localhost:8000/text-to-image \
  -H "Content-Type: application/json" \
  -d '{"text": "A serene mountain lake at sunrise"}' \
  --output image.png
```

### Text-to-Video
```bash
curl -X POST http://localhost:8000/text-to-video \
  -H "Content-Type: application/json" \
  -d '{"text": "A drone shot flying over ocean waves"}' \
  --output video.mp4
```

### Health Check
```bash
curl http://localhost:8000/health
```

---

## Running Unit Tests

```bash
pytest
```

All 17 tests across the adapter factories, custom video pipeline, and generation services will execute.

---

## Docker Deployment

```bash
# Build and run with Docker
docker build -t aimatic-content-gen .
docker run -p 8000:8000 --env-file .env aimatic-content-gen
```

---

## Project Structure

```
.
├── app/
│   ├── adapters/          # External AI provider adapters (AWS, OpenAI, Google)
│   │   ├── image_gen/     # Text-to-Image adapters & factory
│   │   └── video_gen/     # Text-to-Video adapters & factory
│   ├── api/               # FastAPI endpoints, schemas, dependencies, middleware
│   │   ├── dependencies/  # Rate limiting, auth, services DI
│   │   ├── endpoints/     # Content routes & health probes
│   │   └── middleware/    # CORS, drain, request ID
│   ├── config/            # Consolidated settings & feature module registration
│   ├── core/              # Contracts, workflows, custom exceptions
│   ├── observability/     # Structured logging & Prometheus metrics
│   └── services/          # Orchestration layer between API and adapters
├── frontend/              # Vite + React 19 + TypeScript single-page application
├── infra/                 # CloudFormation EC2 templates and CI/CD pipelines
├── tests/                 # Integration tests
├── Dockerfile             # Multi-stage container definition
├── requirements.txt       # Python dependencies
└── DETAILED_DOCUMENTATION.md # In-depth architectural breakdown & audit
```
