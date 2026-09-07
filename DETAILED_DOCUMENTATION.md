# AI Matic — Technical Architecture, Analysis & Execution Guide

## 1. Project Status & "Will This Work Correctly?"

### Status: **WORKING & VERIFIED (All 17 Unit Tests Passing & Frontend Builds Successfully)**

The previously identified startup blockers have been resolved:

| Previous Blocker | Resolution Applied | Verification Status |
|---|---|---|
| Missing `app/config/settings.py` | Created consolidated [settings.py](file:///d:/Projects%20ML/Image%20Generation/app/config/settings.py) inheriting `BaseAppSettings`, `ModelGatewaySettings`, and `ContentSettings` with support for both `TTI_MODEL` and `ACTIVE_TTI_PROVIDER`. | **Resolved** (`get_settings()` loads cleanly). |
| Missing `app/config/features.py` | Created [features.py](file:///d:/Projects%20ML/Image%20Generation/app/config/features.py) registering `content_feature` into `ENABLED_FEATURES`. | **Resolved** (`main.py` imports without error). |
| Missing `app/adapters/common.py` | Created [common.py](file:///d:/Projects%20ML/Image%20Generation/app/adapters/common.py) containing `decode_base64_payload`, `run_sync_in_executor`, and `wrap_provider_error`. | **Resolved** (AWS Bedrock Titan and Nova Reel adapters import and run). |
| Missing Dependencies | Added `mangum>=0.17.0` and `slowapi>=0.1.9` to [requirements.txt](file:///d:/Projects%20ML/Image%20Generation/requirements.txt). | **Resolved**. |
| Missing Provider Adapters | Implemented OpenAI GPT Image client ([openai_gpt_image.py](file:///d:/Projects%20ML/Image%20Generation/app/adapters/image_gen/openai/openai_gpt_image.py)), Google Gemini/Imagen client ([google_gemini_client.py](file:///d:/Projects%20ML/Image%20Generation/app/adapters/image_gen/google_cloud/google_gemini_client.py)), and stubs for Veo and Sora. | **Resolved** (All provider classes load via factory). |
| Route Prefix Alignment | Configured [app/main.py](file:///d:/Projects%20ML/Image%20Generation/app/main.py) to mount routes at both root (`/health`, `/text-to-image`, `/text-to-video`) and prefixed (`/api/health`, `/api/content/...`). | **Resolved** (Both curl and the React UI work). |

### Test Verification
- **Backend Tests**: `pytest` passed 17/17 tests (Factories, Custom Video Pipeline, Image & Video generation services).
- **Frontend Build**: `tsc -b && vite build` built production bundle in 734ms with zero errors.
- **Health Probe**: `curl http://localhost:8000/health` returns `{"status": "ok"}`.

---

## 2. What Is Being Used in AI Matic

AI Matic is an enterprise generative AI microservice foundation designed around **Clean Architecture**, **Dependency Injection**, and a **Provider-Agnostic Factory Pattern**:

```
┌─────────────────────────────────────────────────────────┐
│                    Web Frontend (Vite + React)          │
└────────────────────────────┬────────────────────────────┘
                             │ HTTP JSON / Blobs (/api/...)
┌────────────────────────────▼────────────────────────────┐
│ 1. API Layer (FastAPI Routers, Schemas, Middlewares)    │
│    - Endpoints: /text-to-image, /text-to-video, /health │
│    - Middlewares: CORS, Drain, RequestID, RateLimit     │
└────────────────────────────┬────────────────────────────┘
                             │ Pydantic DTOs
┌────────────────────────────▼────────────────────────────┐
│ 2. Service Layer (Business Orchestration)               │
│    - app/services/content/image_generation_service.py   │
│    - app/services/content/video_generation_service.py   │
└────────────────────────────┬────────────────────────────┘
                             │ Dynamic Factory Resolution
┌────────────────────────────▼────────────────────────────┐
│ 3. Adapter Layer (Factory & Vendor SDKs)                │
│    - AWS Bedrock (Titan Image Generator v2, Nova Reel)  │
│    - OpenAI (DALL-E 3 / GPT Image)                      │
│    - Google Cloud (Gemini / Imagen 3)                   │
│    - Custom Local Pipeline (LTX Transformer, ESRGAN)    │
└────────────────────────────┬────────────────────────────┘
                             │ Binary Streams
┌────────────────────────────▼────────────────────────────┐
│ 4. External Cloud & Model Providers                     │
│    - AWS Bedrock Runtime                                │
│    - OpenAI API                                         │
│    - Google GenAI API                                   │
└─────────────────────────────────────────────────────────┘
```

### Key Libraries & Components:
1. **FastAPI & Uvicorn**: High-performance asynchronous REST API framework and ASGI web server.
2. **Pydantic v2 & Pydantic Settings**: Strict type validation, environment variable ingestion, and config consolidation.
3. **Boto3**: AWS SDK for Amazon Titan Image Generator v2 and Nova Reel video generation jobs.
4. **OpenAI SDK & Google GenAI SDK**: Image synthesis integration for DALL-E and Imagen.
5. **Custom Local Video Pipeline Engine**:
   - `LTX Transformer`: Video diffusion transformer architecture.
   - `LTX VAE Decoder`: Latent-to-pixel video decoding.
   - `T5 Text Encoder`: High-capacity contextual text embeddings.
   - `RealESRGAN Upscaler`: Spatial super-resolution upscaling for video frames.
6. **Observability & Diagnostics**:
   - Structured JSON logging ([app/observability/logging.py](file:///d:/Projects%20ML/Image%20Generation/app/observability/logging.py)).
   - Prometheus metrics hooks ([app/observability/metrics.py](file:///d:/Projects%20ML/Image%20Generation/app/observability/metrics.py)).
   - Tracing hooks (OpenTelemetry, Langfuse, GoML Tracer engine).
7. **Cloud Infrastructure**:
   - `Dockerfile`: Multi-stage Python container.
   - AWS Lambda serverless compatibility via `Mangum`.
   - AWS CloudFormation EC2 template ([infra/DEPLOYMENT/EC2/AIMaticEC2Stack.yml](file:///d:/Projects%20ML/Image%20Generation/infra/DEPLOYMENT/EC2/AIMaticEC2Stack.yml)).
   - GitHub Actions CI/CD pipeline ([infra/CICD/deploy.yml.YML](file:///d:/Projects%20ML/Image%20Generation/infra/CICD/deploy.yml.YML)).

---

## 3. Changes Applied on the Raw Bundle

The complete AI-Matic ecosystem (as found in multi-module suites like `aimatic reel` and `aimatic idp d2d`) is a heavy platform with databases, social media harvesters, and document intelligence.

### 1. What Was Stripped:
- **PostgreSQL Database & ORM**: Removed `SQLAlchemy`, `asyncpg`, Alembic migrations, and database models. The content generation service now operates completely stateless.
- **Redis & Task Workers**: Removed Celery/ARQ/Redis worker dependencies.
- **Scraper Infrastructure**: Stripped Instagram, YouTube, and web scraper modules.
- **Vector Storage**: Stripped Qdrant vector database adapters and RAG indexing.
- **IDP & D2D**: Stripped document-to-document processing, OCR, and table parsers.

### 2. What Was Retained & Adapted:
- Decoupled into a dedicated **Personalized Content Generation microservice** (Text-to-Image & Text-to-Video).
- Retained the `FeatureModule` pluggable modular architecture contract.
- Retained AWS Bedrock Titan & Nova Reel clients and local video synthesis pipeline.

### 3. What Was Added:
- A modern **React 19 + TypeScript + Vite frontend** with interactive prompt suggestions, media preview, history gallery, toast alerts, and responsive dark-theme glassmorphism design.

---

## 4. Features Added

1. **Dual Generation Studio**:
   - High-resolution text-to-image synthesis (PNG output).
   - High-definition text-to-video synthesis (MP4 output).
2. **Interactive UI & Real-Time Feedback**:
   - Tabbed switching between Image and Video modes.
   - Prompt suggestions/chips for immediate testing.
   - Dynamic loading spinners and toast notifications.
3. **In-Browser Session Gallery**:
   - Tracks up to 12 generated assets in session memory.
   - One-click prompt copying and direct asset download.
4. **Memory Management**:
   - Uses native `Blob` and `URL.createObjectURL` with explicit cleanup (`URL.revokeObjectURL`) to prevent browser memory leaks.
5. **Multi-Route Flexibility**:
   - Supports both `/text-to-image` (direct API access) and `/api/content/text-to-image` (frontend microservice access).

---

## 5. About the Frontend

- **Location**: [frontend/](file:///d:/Projects%20ML/Image%20Generation/frontend/)
- **Tech Stack**: React 19, TypeScript, Vite 8, Oxlint, Vanilla CSS.
- **Design Philosophy**: Sleek dark mode, glassmorphism surfaces, CSS custom properties (`index.css`), responsive layouts, micro-animations.
- **Key Modules**:
  - [frontend/src/App.tsx](file:///d:/Projects%20ML/Image%20Generation/frontend/src/App.tsx): Primary controller managing prompt input, media generation, toasts, download handling, and session history gallery.
  - [frontend/src/api.ts](file:///d:/Projects%20ML/Image%20Generation/frontend/src/api.ts): Asynchronous fetch client requesting `/api/content/...` and converting binary responses to Object URLs.
  - [frontend/vite.config.ts](file:///d:/Projects%20ML/Image%20Generation/frontend/vite.config.ts): Development server running on port `5174` with automatic `/api` reverse proxy to `http://localhost:8000`.

---

## 6. Steps to Run the Entire Project

### Step 1: Configure Environment Variables

```powershell
cp .env.example .env
```
Open `.env` and verify provider keys:
```env
TTI_MODEL=titan
TTV_MODEL=nova_reel

AWS_ACCESS_KEY_ID="your_aws_access_key"
AWS_SECRET_ACCESS_KEY="your_aws_secret_key"
AWS_REGION="us-east-1"
```

### Step 2: Start the Backend (FastAPI)

In PowerShell from the project root (`d:\Projects ML\Image Generation`):
```powershell
python -m venv .venv
.venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Swagger Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Probe: [http://localhost:8000/health](http://localhost:8000/health)

### Step 3: Start the Frontend (React + Vite)

In a **separate terminal**:
```powershell
cd "d:\Projects ML\Image Generation\frontend"
npm install
npm run dev
```
- Open your browser at: **[http://localhost:5174](http://localhost:5174)**

### Step 4: Verify End-to-End Generation

1. **Verify Backend Health**:
   ```powershell
   curl http://localhost:8000/health
   ```
   Output: `{"status":"ok"}`
2. **Generate Image via cURL**:
   ```powershell
   curl -X POST http://localhost:8000/text-to-image `
     -H "Content-Type: application/json" `
     -d "{\"text\": \"A glowing neon butterfly on a futuristic circuit board\"}" `
     --output test_image.png
   ```
3. **Generate Image via Web UI**:
   - Open `http://localhost:5174`.
   - Select **Image** or **Video**.
   - Click a prompt chip or type a prompt.
   - Click **Generate Image**. The image will render in real-time and can be downloaded immediately.
