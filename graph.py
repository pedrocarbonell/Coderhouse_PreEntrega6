from typing import Literal, TypedDict

from dotenv import load_dotenv
import os

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from agents.analyst import analyst_node
from agents.researcher import researcher_node
from state import OrchestratorState

from pydantic import SecretStr

load_dotenv()

OPENAI_API_KEY = SecretStr(os.getenv("OPENAI_API_KEY") or "")

MAX_STEPS = 4

SYSTEM_PROMPT = (
    "Eres el supervisor de un orquestador multi-agente. "
    "Trabajadores: researcher (busca datos), analyst (calcula). "
    "Rúbrica estricta:\n"
    "- Si no hay mensaje con name=researcher → next=researcher.\n"
    "- Si hay researcher y no hay analyst → next=analyst.\n"
    "- Si hay ambos y el analyst cita un número basado en datos del researcher → next=FINISH.\n"
    "- Si el analyst no tiene números fuente, envía researcher una sola vez; no loops.\n"
    "Responde solo con el siguiente paso."
)


class Route(TypedDict):
    next: Literal["researcher", "analyst", "FINISH"]


def get_llm() -> ChatOpenAI:
    """Crea el ChatOpenAI del supervisor con la API key del entorno."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=OPENAI_API_KEY.get_secret_value,
    )


router = get_llm().with_structured_output(Route)

def supervisor_node(state: OrchestratorState):
    """Decide el siguiente especialista o FINISH según la rúbrica y el tope de pasos."""
    steps = state.get("steps", 0) + 1
    if steps >= MAX_STEPS:
        return {"next": "FINISH", "steps": steps}

    decision = router.invoke(
        [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    )
    return {"next": decision["next"], "steps": steps}


builder = StateGraph(OrchestratorState)
builder.set_entry_point("supervisor")
builder.add_node("supervisor", supervisor_node)
builder.add_node("researcher", researcher_node)
builder.add_node("analyst", analyst_node)
builder.add_edge("researcher", "supervisor")
builder.add_edge("analyst", "supervisor")

def route_next(state: OrchestratorState) -> Literal["researcher", "analyst", "FINISH"]:
    """Lee state['next'] para las aristas condicionales del supervisor."""
    return state["next"]


builder.add_conditional_edges(
    "supervisor",
    route_next,
    {
        "researcher": "researcher",
        "analyst": "analyst",
        "FINISH": END,
    },
)

graph = builder.compile()
