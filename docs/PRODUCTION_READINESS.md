# IntelliMaint AI — Production Readiness Checklist

This checklist distinguishes repository checks from deployment checks that require access to hosting providers and production infrastructure. Do not mark live checks complete based only on a local test run.

## Repository and continuous integration

- [x] Source code, tests, model artifacts, sample telemetry, and architecture/methodology documentation are version-controlled.
- [x] GitHub Actions workflow is configured to run pytest on pushes and pull requests to `main`.
- [ ] Confirm the first GitHub Actions run completes successfully.
- [ ] Review dependency/security alerts and update dependencies deliberately.
- [ ] Confirm no production credentials, private telemetry, or customer data are committed.
- [ ] Document how the ML model was trained, evaluated, and versioned; ensure reported metrics match reproducible evaluation output.

## Backend and database

- [ ] Configure production `DATABASE_URL` through the hosting provider's secret manager.
- [ ] Use a managed production database with access controls, backups, and a tested restore process.
- [ ] Confirm schema initialization/migration behavior is safe for an existing database.
- [ ] Verify `/health` and API documentation endpoints after deployment.
- [ ] Verify API validation rejects malformed or out-of-range telemetry.
- [ ] Check CORS and network access are restricted to intended clients.
- [ ] Ensure application logs do not expose credentials, full telemetry payloads, or sensitive environment settings.
- [ ] Confirm database errors fail safely and do not return internal stack traces to clients.

## Machine-learning and engineering validity

- [ ] Verify the deployed model artifact matches the metadata and feature order expected by inference code.
- [ ] Run evaluation on a held-out dataset and inspect precision, recall, F1, ROC-AUC, and PR-AUC; do not rely on accuracy alone for imbalanced failure data.
- [ ] Document the model's training dataset, target definition, limitations, and intended use.
- [ ] Clearly label predictions as decision support, not a guarantee of failure or a substitute for qualified engineering inspection.
- [ ] Test missing values, extreme values, units, and sensor inputs outside the training distribution.
- [ ] Confirm risk thresholds and recommended actions are reviewed by a qualified domain expert before operational use.

## Streamlit frontend and reports

- [ ] Configure the frontend API base URL for the deployed backend.
- [ ] Submit a sample telemetry CSV and verify row validation and analysis results.
- [ ] Verify machine registry, risk assessment, maintenance planner, analytics, and report pages against persisted data.
- [ ] Generate a PDF report and confirm units, timestamps, and prediction identifiers are correct.
- [ ] Test the UI at desktop and mobile viewport sizes.

## End-to-end smoke test

1. Start the backend and verify the health endpoint.
2. Start the Streamlit frontend and confirm it reaches the configured backend.
3. Create or select a demo machine and submit sample telemetry.
4. Confirm engineered features and risk output are produced without data leakage or unit confusion.
5. Confirm prediction history and maintenance work orders persist and are linked to the correct machine.
6. Generate a report and compare it with the stored record.
7. Restart the application and verify persisted data remains available.

## Release decision

Release only after the automated CI run is green, the end-to-end smoke test passes, configuration and access controls are reviewed, and model evaluation claims are reproducible. This is an educational engineering portfolio project; do not use it to control industrial equipment or make safety-critical decisions without domain validation, monitoring, and appropriate safeguards.
