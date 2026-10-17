"""
IntelliMaint AI — Frontend API & Database Client

Provides resilient communication to the FastAPI backend with automatic graceful
fallback to direct SQLAlchemy session when the backend API service is offline.
This ensures the Streamlit UI works seamlessly in both standalone and full client-server modes.
"""

from __future__ import annotations
import json
from typing import List, Dict, Any, Optional
import httpx
from backend.app.config import settings
from backend.app.database import SessionLocal
from backend.app.services.machine_service import MachineService
from backend.app.services.telemetry_service import TelemetryService
from backend.app.services.prediction_service import PredictionService
from backend.app.services.maintenance_service import MaintenanceService
from backend.app.services.analytics_service import AnalyticsService
from backend.app.schemas.machine import MachineCreate, MachineUpdate
from backend.app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate
from backend.app.schemas.prediction import PredictionRequest


class IntelliMaintClient:
    def __init__(self, base_url: str = settings.BACKEND_API_BASE_URL, timeout: float = 3.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def check_backend_health(self) -> Dict[str, Any]:
        """Checks if FastAPI backend is reachable, otherwise returns local DB mode status."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/health")
                if resp.status_code == 200:
                    data = resp.json()
                    data["connection_mode"] = "FASTAPI_BACKEND"
                    return data
        except Exception:
            pass

        # Local direct fallback
        return {
            "status": "connected_direct",
            "connection_mode": "DIRECT_DATABASE",
            "app_name": settings.APP_NAME,
            "database": {"status": "healthy", "engine": "sqlite"},
            "machine_learning": {"status": "ready"},
        }

    # ================= MACHINES =================
    def get_machines(self) -> List[Dict[str, Any]]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/machines?limit=500")
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass

        # Fallback to DB
        db = SessionLocal()
        try:
            machines = MachineService.get_all_machines(db, limit=500)
            return [
                {
                    "id": m.id,
                    "machine_id": m.machine_id,
                    "name": m.name,
                    "machine_type": m.machine_type,
                    "department": m.department,
                    "manufacturer": m.manufacturer,
                    "installation_date": m.installation_date,
                    "operational_status": m.operational_status,
                    "notes": m.notes,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "updated_at": m.updated_at.isoformat() if m.updated_at else None,
                }
                for m in machines
            ]
        finally:
            db.close()

    def create_machine(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.base_url}/machines", json=data)
                if resp.status_code in [200, 201]:
                    return resp.json()
                else:
                    return {"error": resp.json().get("detail", "Error creating machine")}
        except Exception:
            pass

        db = SessionLocal()
        try:
            machine_in = MachineCreate(**data)
            created = MachineService.create_machine(db, machine_in)
            return {
                "id": created.id,
                "machine_id": created.machine_id,
                "name": created.name,
                "machine_type": created.machine_type,
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()

    def delete_machine(self, machine_id: str) -> bool:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.delete(f"{self.base_url}/machines/{machine_id}")
                if resp.status_code in [200, 204]:
                    return True
        except Exception:
            pass

        db = SessionLocal()
        try:
            return MachineService.delete_machine(db, machine_id)
        except Exception:
            return False
        finally:
            db.close()

    # ================= FLEET ANALYTICS =================
    def get_fleet_summary(self) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/analytics/summary")
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass

        db = SessionLocal()
        try:
            summary = AnalyticsService.get_fleet_summary(db)
            return summary.model_dump()
        finally:
            db.close()

    # ================= PREDICTIONS =================
    def run_prediction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.base_url}/predictions", json=data)
                if resp.status_code in [200, 201]:
                    return resp.json()
                else:
                    return {"error": resp.json().get("detail", "Prediction failed")}
        except Exception:
            pass

        db = SessionLocal()
        try:
            pred_req = PredictionRequest(**data)
            pred_resp = PredictionService.create_prediction(db, pred_req)
            return pred_resp.model_dump()
        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()

    def get_predictions(self, machine_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            params = f"?limit={limit}"
            if machine_id:
                params += f"&machine_id={machine_id}"
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/predictions{params}")
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass

        db = SessionLocal()
        try:
            records = PredictionService.get_predictions(db, machine_id=machine_id, limit=limit)
            out = []
            for r in records:
                factors = json.loads(r.contributing_factors) if r.contributing_factors else []
                actions = json.loads(r.suggested_actions) if r.suggested_actions else []
                out.append({
                    "prediction_id": r.prediction_id,
                    "machine_id": r.machine_id,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "failure_probability": r.failure_probability,
                    "predicted_failure": r.predicted_failure,
                    "risk_category": r.risk_category,
                    "model_version": r.model_version,
                    "model_algorithm": r.model_algorithm,
                    "contributing_factors": factors,
                    "suggested_actions": actions,
                    "disclaimer": "Educational and portfolio demonstration.",
                })
            return out
        finally:
            db.close()

    # ================= TELEMETRY =================
    def get_telemetry(self, machine_id: Optional[str] = None, limit: int = 500) -> List[Dict[str, Any]]:
        try:
            params = f"?limit={limit}"
            if machine_id:
                params += f"&machine_id={machine_id}"
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/telemetry{params}")
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass

        db = SessionLocal()
        try:
            records = TelemetryService.get_telemetry_records(db, machine_id=machine_id, limit=limit)
            return [
                {
                    "id": r.id,
                    "machine_id": r.machine_id,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "air_temperature": r.air_temperature,
                    "process_temperature": r.process_temperature,
                    "rotational_speed": r.rotational_speed,
                    "torque": r.torque,
                    "tool_wear": r.tool_wear,
                    "machine_type_variant": r.machine_type_variant,
                    "temp_diff": r.temp_diff,
                    "mechanical_power": r.mechanical_power,
                    "strain_product": r.strain_product,
                    "failure_prediction": r.failure_prediction,
                    "failure_probability": r.failure_probability,
                    "risk_tier": r.risk_tier,
                }
                for r in records
            ]
        finally:
            db.close()

    def upload_telemetry_csv(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        try:
            files = {"file": (filename, file_bytes, "text/csv")}
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(f"{self.base_url}/telemetry/upload", files=files)
                if resp.status_code == 200:
                    return resp.json()
                else:
                    return {"error": resp.json().get("detail", "Upload failed")}
        except Exception:
            pass

        db = SessionLocal()
        try:
            valid_df, errors = TelemetryService.validate_and_parse_csv(file_bytes, filename=filename)
            summary = TelemetryService.ingest_validated_df(db, valid_df, filename=filename)
            summary.error_details = errors[:10]
            return summary.model_dump()
        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()

    # ================= MAINTENANCE =================
    def get_maintenance_tasks(
        self,
        machine_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        try:
            params = f"?limit={limit}"
            if machine_id:
                params += f"&machine_id={machine_id}"
            if status_filter:
                params += f"&status={status_filter}"
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/maintenance{params}")
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass

        db = SessionLocal()
        try:
            tasks = MaintenanceService.get_tasks(db, machine_id=machine_id, status_filter=status_filter, limit=limit)
            return [
                {
                    "id": t.id,
                    "work_order_no": t.work_order_no,
                    "machine_id": t.machine_id,
                    "title": t.title,
                    "description": t.description,
                    "priority": t.priority,
                    "technician": t.technician,
                    "due_date": t.due_date,
                    "status": t.status,
                    "notes": t.notes,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                }
                for t in tasks
            ]
        finally:
            db.close()

    def create_maintenance_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.base_url}/maintenance", json=data)
                if resp.status_code in [200, 201]:
                    return resp.json()
                else:
                    return {"error": resp.json().get("detail", "Failed to create work order")}
        except Exception:
            pass

        db = SessionLocal()
        try:
            task_in = MaintenanceCreate(**data)
            created = MaintenanceService.create_task(db, task_in)
            return {
                "id": created.id,
                "work_order_no": created.work_order_no,
                "machine_id": created.machine_id,
                "title": created.title,
                "status": created.status,
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()

    def update_maintenance_task(self, task_id_or_no: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.patch(f"{self.base_url}/maintenance/{task_id_or_no}", json=data)
                if resp.status_code == 200:
                    return resp.json()
                else:
                    return {"error": resp.json().get("detail", "Failed to update work order")}
        except Exception:
            pass

        db = SessionLocal()
        try:
            task_in = MaintenanceUpdate(**data)
            updated = MaintenanceService.update_task(db, task_id_or_no, task_in)
            return {
                "id": updated.id,
                "work_order_no": updated.work_order_no,
                "status": updated.status,
                "notes": updated.notes,
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()


# Global client instance
api_client = IntelliMaintClient()
