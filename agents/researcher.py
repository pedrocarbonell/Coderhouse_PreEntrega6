from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from state import OrchestratorState

load_dotenv()

CORPUS = {
    "acme": "Acme ventas 2023: 100; Acme ventas 2024: 120",
}


@tool
def search_corpus(query: str) -> str:
    """Busca datos en el corpus local de ventas."""
    q = query.lower()
    for key, value in CORPUS.items():
        if key in q:
            return value
    return "sin datos"


def get_llm() -> ChatOpenAI:
    """Crea el ChatOpenAI del agente de investigación."""
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


researcher = create_react_agent(
    get_llm(),
    tools=[search_corpus],
    prompt=(
        "Eres el agente de investigación. Solo usa search_corpus. "
        "Devuelve únicamente los datos crudos encontrados. "
        "No calcules porcentajes ni analices."
    ),
)


def researcher_node(state: OrchestratorState):
    """Invoca al investigador y guarda solo el hallazgo final en el estado."""
    result = researcher.invoke({"messages": state["messages"][-2:]})
    last = result["messages"][-1]
    return {"messages": [HumanMessage(content=last.content, name="researcher")]}
