# Security Policy

## Supported Version

Security fixes target the latest code on the default `main` branch.

## Reporting a Vulnerability

Please do not publish exploitable vulnerabilities, credentials, private telemetry, or personal data in a public issue.

Use GitHub's **Report a vulnerability** option on this repository when private vulnerability reporting is available. Include:
- A concise description and potential impact.
- Reproduction steps or a minimal proof of concept.
- Affected files, endpoints, and configuration.
- Any safe mitigation you have identified.

Please allow time for investigation before publicly disclosing a confirmed vulnerability.

## Safe Deployment

- Keep real credentials in environment variables or the hosting provider's secret manager.
- Never commit `.env` files, database exports, access tokens, or private industrial telemetry.
- Replace example secrets before deployment and use a unique, high-entropy secret.
- Restrict database network access and use TLS where supported.
- Keep dependencies updated and review GitHub security alerts.
- Treat this educational project as decision-support software only; do not connect it directly to safety-critical machinery without independent engineering validation.
