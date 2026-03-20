# OpenBiometrics

Open-source biometric platform for developers. Face recognition, document processing, liveness detection, video analytics, and identity verification — as simple as an API call.

**[Documentation](https://drinkredwine.github.io/openbiometrics/)** | **[Quickstart](https://drinkredwine.github.io/openbiometrics/quickstart/)** | **[API Reference](https://drinkredwine.github.io/openbiometrics/api/face-detection/)**

## Features

- **Face Detection** — SCRFD detector with quality scoring, landmarks, demographics
- **Face Recognition** — ArcFace embeddings (99.86% LFW), 1:1 verification and 1:N identification
- **Passive Liveness** — MiniFASNet anti-spoofing, no user interaction
- **Active Liveness** — Challenge-response with 7 action types and presets (blink, smile, head turn)
- **Document Processing** — MRZ parsing (ICAO 9303), OCR, document detection for passports/IDs
- **Video Analytics** — Multi-camera management with real-time face processing
- **Events & Webhooks** — Event bus with HMAC-signed webhook delivery
- **Watchlists** — FAISS-powered similarity search, identity resolution, deduplication
- **Edge Ready** — Docker, Jetson, ARM via ONNX Runtime / TensorRT / NCNN

## Quick Start

```bash
# Clone and install
git clone https://github.com/drinkredwine/openbiometrics
cd openbiometrics
cd engine && pip install -e . && python download_models.py
cd ../api && uvicorn app.main:app --port 8000
```

```bash
# Detect faces
curl -X POST http://localhost:8000/api/v1/detect -F "image=@photo.jpg"
```

## SDKs

### Node.js
```ts
import { OpenBiometrics } from 'openbiometrics';

const ob = new OpenBiometrics({ apiKey: 'any', baseUrl: 'http://localhost:8000' });
const { faces } = await ob.faces.detect(photoBuffer);
const { is_match } = await ob.faces.verify(id, selfie);
await ob.watchlists.enroll(photo, { label: 'Alice' });
const { matches } = await ob.watchlists.identify(unknown);
```

### Python
```python
from openbiometrics_sdk import OpenBiometrics

ob = OpenBiometrics(api_key="any", base_url="http://localhost:8000")
result = ob.faces.detect("photo.jpg")
result = ob.faces.verify("id.jpg", "selfie.jpg")
ob.watchlists.enroll("photo.jpg", label="Alice")
result = ob.watchlists.identify("unknown.jpg")
```

## Project Structure

```
openbiometrics/
├── engine/              # Core biometric engine (Python)
│   └── openbiometrics/  # Face, documents, liveness, video, events, identity
├── api/                 # FastAPI REST server
├── packages/
│   ├── dashboard/       # React admin UI
│   ├── sdk/             # Node.js SDK (npm install openbiometrics)
│   ├── www/             # Documentation site (Astro + Starlight)
│   ├── sample-kyc/      # KYC onboarding demo
│   ├── sample-2fa/      # Face 2FA login demo
│   ├── sample-age-gate/ # Age verification demo
│   ├── sample-visitor-log/    # Visitor management demo
│   └── sample-surveillance/   # Surveillance dashboard demo
├── sdks/
│   └── python/          # Python SDK (pip install openbiometrics)
└── tests/
```

## Development

```bash
# Run all services (API + dashboard + docs)
mprocs --config mprocs.yaml
```

| Service | URL |
|---------|-----|
| API + Swagger | http://localhost:8000/docs |
| Dashboard | http://localhost:3600 |
| Docs | http://localhost:4000 |

## Models

The engine uses ONNX models from InsightFace:

| Model | Size | Purpose |
|-------|------|---------|
| SCRFD (det_10g) | 16 MB | Face detection |
| ArcFace (w600k_r50) | 166 MB | Face recognition |
| GenderAge | 1.3 MB | Demographics |
| MiniFASNet | 2 MB | Passive liveness |
| YOLOv8n | 12 MB | Person detection |
| Face Mesh | 2.8 MB | Active liveness landmarks |

## License

[MIT](LICENSE)
