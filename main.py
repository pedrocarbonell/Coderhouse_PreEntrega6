from langchain_core.messages import HumanMessage

from graph import graph
from state import OrchestratorState

QUERY = (
    "Busca las ventas de Acme en 2023 y 2024 y calcula el cambio porcentual."
)


def main() -> None:
    initial: OrchestratorState = {
        "messages": [HumanMessage(content=QUERY)],
        "steps": 0,
        "next": "researcher",
    }
    for update in graph.stream(
        initial,
        config={"recursion_limit": 12},
        stream_mode="updates",
    ):
        for node, payload in update.items():
            print(f"\n=== {node} ===")
            if "next" in payload:
                print(f"next={payload['next']} steps={payload.get('steps')}")
            for msg in payload.get("messages", []):
                name = getattr(msg, "name", None) or type(msg).__name__
                print(f"[{name}] {msg.content}")


if __name__ == "__main__":
    main()
