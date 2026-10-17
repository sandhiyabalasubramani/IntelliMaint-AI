# IntelliMaint AI — System Architecture & Technical Specifications

## 1. System Overview

**IntelliMaint AI** is an intelligent, physics-informed industrial predictive maintenance decision-support platform. It bridges electrical power telemetry, thermodynamic heat convection dynamics, and mechanical degradation physics to forecast industrial machine breakdown risk before unplanned downtime occurs.

The platform is architected with a decoupled full-stack design consisting of:
- **Interactive Multi-Page Presentation Layer:** Built with Streamlit, Plotly, and custom CSS design tokens tailored for industrial control rooms.
- **RESTful Application Programming Interface (API):** Built with FastAPI, Pydantic v2 validation, and OpenAPI 3.1 documentation.
- **Data Persistence Layer:** SQLAlchemy 2.x ORM supporting zero-configuration local SQLite as well as enterprise PostgreSQL via connection string configuration.
- **Machine Learning & Feature Engineering Pipeline:** Scikit-learn Pipeline incorporating mathematical domain features ($\Delta T$, mechanical cutting power $P$, strain product) and serialized Gradient Boosting ensemble models.
- **Reporting & Compliance Engine:** ReportLab document compiler generating formal, multi-section PDF maintenance inspection certificates.

---

## 2. Component Architecture Diagram

```mermaid
graph TD
    subgraph Client ["Client Presentation Layer (Streamlit :8501)"]
        UI_Fleet["Fleet Health Dashboard"]
        UI_Registry["Machine Asset Registry"]
        UI_Upload["Telemetry CSV Ingestion"]
        UI_Risk["Real-Time Risk Simulator"]
        UI_Planner["Maintenance Work Order Planner"]
        UI_Analytics["Analytics & Sensor Trends"]
        UI_Reports["Inspection Reports & Audit Trail"]
        UI_About["Methodology & Physics Documentation"]
    end

    subgraph Client_Utils ["Client Communications & Utilities"]
        API_Client["Resilient API & Database Client\n(HTTPX / Direct Fallback)"]
        PDF_Engine["ReportLab PDF Generator"]
    end

    subgraph Backend ["Application Backend (FastAPI / Uvicorn :8000)"]
        Router_Health["/health"]
        Router_Machines["/api/v1/machines"]
        Router_Telemetry["/api/v1/telemetry"]
        Router_Predictions["/api/v1/predictions"]
        Router_Maintenance["/api/v1/maintenance"]
        Router_Analytics["/api/v1/analytics"]
    end

    subgraph Services ["Domain Services & Business Logic"]
        SVC_Machine["MachineService"]
        SVC_Telemetry["TelemetryService & Validation"]
        SVC_Prediction["PredictionService"]
        SVC_Maintenance["MaintenanceService (Lifecycle Validation)"]
        SVC_Analytics["AnalyticsService"]
    end

    subgraph ML_Engine ["Machine Learning Inference Engine"]
        Predictor["FailureRiskPredictor"]
        Feature_Eng["EngineeringFeaturesTransformer\n(Delta T, Power W, Strain)"]
        GB_Model["Gradient Boosting Champion Model\n(best_model.joblib)"]
        Metadata["model_metadata.json"]
    end

    subgraph Persistence ["Persistence Layer (SQLAlchemy 2.x)"]
        DB_Engine[("Database Engine\nSQLite Default / PostgreSQL")]
        Table_Machines[("machines")]
        Table_Telemetry[("telemetry_records")]
        Table_Predictions[("predictions")]
        Table_Maintenance[("maintenance_tasks")]
    end

    Client --> API_Client
    Client_Utils --> PDF_Engine
    API_Client -- "REST HTTP Requests" --> Backend
    Backend --> Services
    Services --> Persistence
    SVC_Telemetry --> Predictor
    SVC_Prediction --> Predictor
    Predictor --> Feature_Eng
    Feature_Eng --> GB_Model
    Predictor --> Metadata
    Persistence --> DB_Engine
    DB_Engine --> Table_Machines
    DB_Engine --> Table_Telemetry
    DB_Engine --> Table_Predictions
    DB_Engine --> Table_Maintenance
```

---

## 3. Database Schema & Entity Relationships

The relational persistence schema is structured around 4 primary entities enforcing foreign key constraints and cascade rules:

```mermaid
erDiagram
    MACHINES ||--o{ TELEMETRY_RECORDS : "records"
    MACHINES ||--o{ PREDICTIONS : "assesses"
    MACHINES ||--o{ MAINTENANCE_TASKS : "dispatches"

    MACHINES {
        int id PK
        string machine_id UK "Unique Identifier"
        string name "Asset Name"
        string machine_type "Equipment Category"
        string department "Facility Cell Location"
        string manufacturer "OEM Manufacturer"
        string installation_date "YYYY-MM-DD"
        string operational_status "OPERATIONAL / DEGRADED / MAINTENANCE / OFFLINE"
        text notes "Operational notes"
        datetime created_at
        datetime updated_at
    }

    TELEMETRY_RECORDS {
        int id PK
        string machine_id FK "References machines.machine_id"
        datetime timestamp "Ingestion Timestamp"
        float air_temperature "Air Temp (K)"
        float process_temperature "Process Temp (K)"
        float rotational_speed "RPM"
        float torque "Torque (Nm)"
        float tool_wear "Tool Wear (min)"
        string machine_type_variant "L / M / H Quality"
        float temp_diff "Delta T (K)"
        float mechanical_power "Power (W)"
        float strain_product "Torque x Wear"
        int failure_prediction "0 or 1"
        float failure_probability "0.00 to 1.00"
        string risk_tier "Low / Medium / High"
        string source_file "Batch Origin"
    }

    PREDICTIONS {
        int id PK
        string prediction_id UK "PRED-XXXXXXXX"
        string machine_id FK "References machines.machine_id"
        datetime timestamp "Assessment Time"
        float failure_probability "Estimated Hazard Probability"
        int predicted_failure "Binary Indicator"
        string risk_category "Low / Medium / High"
        string model_version "Model Release Version"
        string model_algorithm "Classifier Name"
        text contributing_factors "JSON Array of Root Causes"
        text suggested_actions "JSON Array of Corrective Actions"
        text input_telemetry "JSON Snapshot of Ingested Readings"
    }

    MAINTENANCE_TASKS {
        int id PK
        string work_order_no UK "WO-YYYY-XXXX"
        string machine_id FK "References machines.machine_id"
        string title "Work Order Scope"
        text description "Detailed problem description"
        string priority "Low / Medium / High / Critical"
        string technician "Assigned Engineer / Tech"
        string due_date "Target Resolution Date"
        string status "Open / In Progress / Completed / Cancelled"
        text notes "Resolution and root-cause logs"
        datetime created_at
        datetime updated_at
        datetime completed_at
    }
```

---

## 4. REST API Endpoint Catalog

All routes are documented and testable interactively via Swagger UI at `/docs`.

| Method | Endpoint | Description | Request / Query Body | Response Code |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | System health, database connection, and ML status | None | 200 OK |
| `GET` | `/api/v1/machines` | List all registered machines in the fleet | `skip`, `limit` | 200 OK |
| `POST` | `/api/v1/machines` | Register a new machine asset | `MachineCreate` JSON | 201 Created |
| `GET` | `/api/v1/machines/{id}` | Retrieve details of a specific machine | `machine_id` path param | 200 OK / 404 |
| `PATCH`| `/api/v1/machines/{id}` | Update machine status or notes | `MachineUpdate` JSON | 200 OK / 404 |
| `DELETE`| `/api/v1/machines/{id}`| Remove machine and cascade related telemetry | `machine_id` path param | 204 No Content |
| `GET` | `/api/v1/telemetry` | Query historical telemetry readings | `machine_id`, `risk_tier`, `limit` | 200 OK |
| `POST` | `/api/v1/telemetry` | Record single telemetry reading with auto-eval | `TelemetryCreate` JSON | 201 Created |
| `POST` | `/api/v1/telemetry/upload` | Upload and validate batch CSV telemetry | `multipart/form-data` (file) | 200 OK / 422 |
| `GET` | `/api/v1/predictions` | Query historical failure predictions | `machine_id`, `risk_category`, `limit` | 200 OK |
| `POST` | `/api/v1/predictions` | Run real-time ML risk assessment and persist | `PredictionRequest` JSON | 201 Created / 503 |
| `GET` | `/api/v1/predictions/{id}` | Get single prediction assessment by ID | `prediction_id` path param | 200 OK / 404 |
| `GET` | `/api/v1/maintenance` | List maintenance work orders | `machine_id`, `status`, `priority` | 200 OK |
| `POST` | `/api/v1/maintenance` | Create a new maintenance work order | `MaintenanceCreate` JSON | 201 Created |
| `PATCH`| `/api/v1/maintenance/{id}` | Update work order status and completion notes | `MaintenanceUpdate` JSON | 200 OK / 400 |
| `GET` | `/api/v1/analytics/summary` | Real-time database fleet KPIs and overview | None | 200 OK |
