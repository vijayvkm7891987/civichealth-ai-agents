import datetime
import uuid
from typing import Any, Dict, List

# In-memory store for local dev; swap with google.cloud.firestore.Client() in production
DB: Dict[str, Any] = {
    "tickets": {
        "REQ-2026-8841": {
            "id": "REQ-2026-8841",
            "type": "Water Quality & Chlorination Check",
            "ward": "Ward 14 - North Zone",
            "status": "IN_PROGRESS",
            "eta": "Today, 17:30 IST",
        }
    },
    "handoff_queue": [],
    "incidents": [],
    "sops": {
        "SOP-WB-04": {
            "code": "SOP-WB-04 (Rev 2026.2)",
            "title": "Acute Waterborne Cluster Investigation",
            "steps": [
                "Deploy rapid response team within 2 hours for >=3 linked GI/febrile cases in one ward.",
                "Collect paired water samples (source + household tap) for residual chlorine and coliform testing.",
                "Issue immediate boil-water advisory and distribute ORS + chlorine tablets.",
            ],
        },
        "SOP-VB-11": {
            "code": "SOP-VB-11 (Rev 2026.1)",
            "title": "Dengue / Vector Larval Containment",
            "steps": [
                "Conduct indoor/outdoor larval survey within 100m radius of index case.",
                "Apply temephos larvicide to non-potable water containers and log GPS coordinates.",
            ],
        },
    },
}


# --- CUSTOMER AGENT TOOLS ---


def lookup_service_request(request_id: str) -> Dict[str, Any]:
    """Look up the live status of a citizen public health or sanitation request."""
    ticket = DB["tickets"].get(request_id.upper())
    if not ticket:
        return {"found": False, "message": f"No request found matching {request_id}."}
    return {"found": True, "ticket": ticket}


def book_clinic_slot(
    citizen_name: str, clinic_ward: str, service_type: str, preferred_date: str
) -> Dict[str, Any]:
    """Book a primary health clinic appointment or vaccination slot."""
    booking_id = f"APT-{uuid.uuid4().hex[:6].upper()}"
    return {
        "confirmed": True,
        "booking_id": booking_id,
        "citizen_name": citizen_name,
        "clinic_ward": clinic_ward,
        "service_type": service_type,
        "scheduled_date": preferred_date,
    }


def triage_symptom_cluster(
    symptoms: List[str], affected_count: int, ward: str, duration_hours: int
) -> Dict[str, Any]:
    """Evaluate symptom severity and epidemiological cluster thresholds."""
    red_flags = {"difficulty breathing", "chest pain", "bloody diarrhea", "unconscious"}
    has_red_flag = any(s.lower() in red_flags for s in symptoms)
    is_cluster = affected_count >= 3

    urgency = "ROUTINE"
    if has_red_flag or (is_cluster and duration_hours >= 12):
        urgency = "CRITICAL"
    elif is_cluster or duration_hours >= 48:
        urgency = "HIGH"

    return {
        "urgency": urgency,
        "is_cluster_alert": is_cluster,
        "recommended_sop": "SOP-WB-04" if is_cluster else "SOP-GEN-01",
        "escalate_immediately": urgency in {"CRITICAL", "HIGH"},
    }


def escalate_to_frontline(
    session_id: str, citizen_summary: str, urgency: str, ward: str
) -> Dict[str, Any]:
    """Escalate an urgent citizen conversation to the Frontline Officer queue."""
    case_id = f"ESC-{uuid.uuid4().hex[:5].upper()}"
    record = {
        "case_id": case_id,
        "session_id": session_id,
        "summary": citizen_summary,
        "urgency": urgency.upper(),
        "ward": ward,
        "status": "AWAITING_OFFICER",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    DB["handoff_queue"].insert(0, record)
    return {"escalated": True, "case_id": case_id, "queue_position": 1}


# --- FRONTLINE AGENT TOOLS ---


def search_health_sop(topic_or_code: str) -> Dict[str, Any]:
    """Retrieve official public health Standard Operating Procedures by code or keyword."""
    query = topic_or_code.lower()
    matches = [
        sop
        for code, sop in DB["sops"].items()
        if query in code.lower()
        or query in sop["title"].lower()
        or any(query in s.lower() for s in sop["steps"])
    ]
    return {"matches": matches or list(DB["sops"].values())}


def summarize_case_handoff(case_id: str) -> Dict[str, Any]:
    """Fetch full context and triage metadata for an escalated citizen case."""
    for item in DB["handoff_queue"]:
        if item["case_id"] == case_id.upper():
            return {"found": True, "case": item}
    return {"found": False, "queue": DB["handoff_queue"]}


def file_field_incident(
    officer_id: str, ward: str, category: str, findings: str, samples_collected: bool
) -> Dict[str, Any]:
    """Create a structured epidemiological or sanitation field inspection record."""
    incident_id = f"INC-{uuid.uuid4().hex[:6].upper()}"
    incident = {
        "incident_id": incident_id,
        "officer_id": officer_id,
        "ward": ward,
        "category": category,
        "findings": findings,
        "samples_collected": samples_collected,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    DB["incidents"].append(incident)
    return {"recorded": True, "incident": incident}


CUSTOMER_TOOLS = [
    lookup_service_request,
    book_clinic_slot,
    triage_symptom_cluster,
    escalate_to_frontline,
]

FRONTLINE_TOOLS = [
    search_health_sop,
    summarize_case_handoff,
    file_field_incident,
]
