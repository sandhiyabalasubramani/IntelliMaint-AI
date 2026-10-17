# Demo Screenshots & Walkthrough Recording

This checklist keeps the repository's visual evidence authentic to the running application. Do not use mock UI renders as screenshots of the live product.

## Capture checklist

Capture these screens after starting the backend and Streamlit frontend using the commands in [Deployment](DEPLOYMENT.md):

1. **Fleet overview** — KPI cards, risk distribution, fleet summary.
2. **Machine registry** — representative asset rows with no private or real facility data.
3. **Telemetry analysis** — upload the included sample CSV and show the analysis result.
4. **Risk assessment** — show a prediction, probability, and contributing factors.
5. **Maintenance planner** — show a demo work order and its lifecycle.
6. **Analytics and report** — chart view and a generated sample PDF report.

## Suggested repository paths

- Screenshots: `assets/screenshots/fleet-dashboard.png`, `machine-registry.png`, `telemetry-analysis.png`, `risk-assessment.png`, `maintenance-planner.png`, `analytics-report.png`
- Walkthrough: `assets/demo/intellimaint-walkthrough.mp4`

Only add files after they have been captured from the actual running app. Keep images readable at desktop width, crop out unrelated windows, and use seeded demo data rather than personal or production data.

## Windows capture workflow

- **Screenshot:** use Snipping Tool (`Win + Shift + S`) and save the captured image as PNG.
- **Screen recording:** use Xbox Game Bar (`Win + Alt + R`) where available, or another trusted screen recorder. Record a short 60–120 second flow: fleet overview → telemetry analysis → risk assessment → work order → report.
- Close terminals that display secrets, hide personal notifications, and never show `.env`, API keys, passwords, database credentials, or private user data.
- Review the recording before publishing; confirm the demo contains no secrets and that displayed outputs are genuinely produced by the app.

## Add media to GitHub

Place the captured files at the paths above, then commit them with a message such as `docs: add application screenshots and walkthrough`. The README can then embed the real screenshots and link the MP4. Until those files exist, the architecture diagram is the only repository visual and is not presented as an application screenshot.
