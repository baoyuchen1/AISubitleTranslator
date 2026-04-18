# Security Policy

## Supported Use

This repository is a desktop utility project and does not provide a hosted service.

## Sensitive Data

Never commit:

- `.env`
- API keys
- access tokens
- private logs containing credentials

The repository already ignores common local secrets and build output through `.gitignore`.

## Reporting

If you discover:

- accidental credential exposure
- unsafe secret handling
- remote code execution issues
- dependency-related security risks

please report it privately to the repository owner before opening a public issue.

## Recommendations For Users

- Store your real keys only in `.env`
- Rotate any key immediately if you think it was exposed
- Review `git status` before every commit
