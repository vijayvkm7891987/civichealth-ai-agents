import os
from typing import Dict, List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents import run_agent_turn
from tools import DB

app = FastAPI(title="CivicHealth Dual-Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    role: str  # "customer" or "frontline"
    session_id: str
    message: str
    history: List[Dict[str, str]] = []


class OfficerReplyRequest(BaseModel):
    case_id: str
    officer_name: str
    reply_text: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "civichealth-dual-agent"}


@app.post("/api/chat")
def chat(req: ChatRequest):
    result = run_agent_turn(role=req.role, message=req.message, history=req.history)
    return {
        "session_id": req.session_id,
        "role": req.role,
        "reply": result["reply"],
        "tool_calls": result["tool_calls"],
        "handoff_queue": DB["handoff_queue"],
    }


@app.get("/api/queue")
def get_queue():
    return {"handoff_queue": DB["handoff_queue"], "incidents": DB["incidents"]}


@app.post("/api/handoff/reply")
def officer_reply(req: OfficerReplyRequest):
    for item in DB["handoff_queue"]:
        if item["case_id"] == req.case_id:
            item["status"] = "OFFICER_RESPONDED"
            item["officer_reply"] = req.reply_text
            item["handled_by"] = req.officer_name
            return {"updated": True, "case": item}
    return {"updated": False}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
