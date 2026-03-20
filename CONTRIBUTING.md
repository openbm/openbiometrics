# Contributing to OpenBiometrics

Thanks for your interest in contributing!

## Getting Started

1. Fork the repo
2. Clone your fork
3. Install dependencies:
   ```bash
   cd engine && pip install -e ".[dev]"
   cd ../packages/dashboard && npm install
   cd ../packages/sdk && npm install
   cd ../packages/www && npm install
   ```
4. Run: `mprocs --config mprocs.yaml`

## Structure

- **engine/** — Python biometric engine. Changes here affect the core ML pipeline.
- **api/** — FastAPI routes. Add new endpoints in `api/app/routes/`.
- **packages/sdk/** — Node.js SDK. Keep in sync with API changes.
- **sdks/python/** — Python SDK. Keep in sync with API changes.
- **packages/www/** — Docs site. Update when adding/changing API endpoints.

## Pull Requests

- Keep PRs focused — one feature or fix per PR
- Update docs if you change the API surface
- Update both SDKs (Node.js + Python) if you add endpoints
- Add tests for new engine features in `tests/`

## Versioning

All packages share a single version number. Don't bump versions in PRs — maintainers handle releases.

## License

By contributing, you agree that your contributions will be licensed under MIT.
