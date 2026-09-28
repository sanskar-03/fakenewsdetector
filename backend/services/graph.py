from langgraph.graph import StateGraph, END
from backend.services.graph_state import VerificationState
from backend.services.agents import (
    text_verifier_node, image_verifier_node,
    fact_check_retriever_node, source_credibility_node,
)

def build_verification_graph():
    graph = StateGraph(VerificationState)
    graph.add_node("text_verifier", text_verifier_node)
    graph.add_node("fact_check_retriever", fact_check_retriever_node)
    graph.add_node("image_verifier", image_verifier_node)
    graph.add_node("source_credibility", source_credibility_node)
    graph.set_entry_point("text_verifier")
    graph.add_edge("text_verifier", "fact_check_retriever")
    graph.add_edge("fact_check_retriever", "image_verifier")
    graph.add_edge("image_verifier", "source_credibility")
    graph.add_edge("source_credibility", END)
    return graph.compile()

verification_graph = build_verification_graph()
