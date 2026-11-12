from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from state import OrchestratorState

load_dotenv()


@tool
def percent_change(previous: float, current: float) -> str:
    """Calcula el cambio porcentual: ((current - previous) / previous) * 100."""
    if previous == 0:
        return "error: previous no puede ser 0"
    return str(((current - previous) / previous) * 100)


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


analyst = create_react_agent(
    get_llm(),
    tools=[percent_change],
    prompt=(
        "Eres el agente de análisis. Solo usa percent_change con números "
        "que ya estén en el contexto. No inventes cifras."
    ),
)


def analyst_node(state: OrchestratorState):
    result = analyst.invoke({"messages": state["messages"][-2:]})
    last = result["messages"][-1]
    return {"messages": [HumanMessage(content=last.content, name="analyst")]}


if __name__ == "__main__":
    assert percent_change.invoke({"previous": 100.0, "current": 120.0}) == "20.0"
    print("ok")
