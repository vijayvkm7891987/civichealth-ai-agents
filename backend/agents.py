import os
from typing import Any, Dict, List
from google import genai
from google.genai import types
from tools import CUSTOMER_TOOLS, FRONTLINE_TOOLS

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

MODEL_ID = "gemini-2.5-flash"

CUSTOMER_SYSTEM_PROMPT = """You are CivicHealth Citizen Assistant, an empathetic public health triage and municipal service agent.
- Use `lookup_service_request` for ticket tracking and `book_clinic_slot` for appointments.
- Always run `triage_symptom_cluster` when symptoms or illness clusters are described.
- If `escalate_immediately` is true, call `escalate_to_frontline` immediately and inform the citizen an officer is reviewing their case.
- Never provide definitive medical diagnoses."""

FRONTLINE_SYSTEM_PROMPT = """You are CivicHealth Frontline Copilot assisting public health officers and field workers.
- Always ground protocol answers using `search_health_sop` and cite exact SOP codes.
- Use `summarize_case_handoff` to brief officers taking over citizen escalations.
- Structure field observations into official records with `file_field_incident`."""


def run_agent_turn(role: str, message: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
    """Execute one conversational turn with automatic Gemini function calling."""
    is_frontline = role == "frontline"
    system_instruction = FRONTLINE_SYSTEM_PROMPT if is_frontline else CUSTOMER_SYSTEM_PROMPT
    tools = FRONTLINE_TOOLS if is_frontline else CUSTOMER_TOOLS

    contents: List[types.Content] = []
    for turn in history:
        contents.append(
            types.Content(
                role=turn["role"],
                parts=[types.Part.from_text(text=turn["text"])],
            )
        )
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=tools,
            temperature=0.2,
        ),
    )

    tool_trace = []
    if response.automatic_function_calling_history:
        for item in response.automatic_function_calling_history:
            for part in item.parts:
                if part.function_call:
                    tool_trace.append(
                        {"tool": part.function_call.name, "args": dict(part.function_call.args)}
                    )

    return {
        "reply": response.text,
        "tool_calls": tool_trace,
    }
