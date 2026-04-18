# Contributing

## Scope

Useful contributions include:

- OCR accuracy improvements
- GUI polish
- packaging fixes
- subtitle parsing and export improvements
- translation provider integrations

## Development Setup

```powershell
py -3.9 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
Copy-Item .env.example .env
```

## Rules

- Do not commit real API keys or `.env`
- Keep Windows support working
- Prefer small focused pull requests
- Preserve existing user files and local configuration

## Before Opening a PR

- Run the app locally
- Verify the target workflow still works
- Update documentation if behavior changed

## Areas That Need Help

- Better OCR preprocessing
- More subtitle formats such as ASS
- Better overlay styling
- Model/provider adapters beyond OpenAI-compatible APIs
