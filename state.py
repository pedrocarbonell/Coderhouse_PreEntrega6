from typing import Literal

from langgraph.graph import MessagesState


class OrchestratorState(MessagesState):
    next: Literal["researcher", "analyst", "FINISH"]
    steps: int
