"""
Assemblage du workflow agentique LangGraph pour AutoClaim.
Orchestre les nœuds, gère les flux conditionnels et l'interruption Human-in-the-Loop.
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from src.schemas.state import AgentState
from src.agent.nodes import (
    node_verify_access,
    node_analyze_image_and_query,
    node_retrieve_sources,
    node_rerank_sources,
    node_consult_mcp_history,
    node_synthesize_and_verify,
    node_execute_mcp_action
)

def build_autoclaim_graph():
    """Construit et compile le graphe d'états LangGraph."""
    workflow = StateGraph(AgentState)

    # Ajout des nœuds
    workflow.add_node("verify_access", node_verify_access)
    workflow.add_node("analyze_image_and_query", node_analyze_image_and_query)
    workflow.add_node("retrieve_sources", node_retrieve_sources)
    workflow.add_node("rerank_sources", node_rerank_sources)
    workflow.add_node("consult_mcp_history", node_consult_mcp_history)
    workflow.add_node("synthesize_and_verify", node_synthesize_and_verify)
    workflow.add_node("execute_mcp_action", node_execute_mcp_action)

    # Définition du point d'entrée
    workflow.set_entry_point("verify_access")

    # Branche conditionnelle après vérification d'accès
    def route_after_access(state: AgentState):
        if state.is_prompt_injection_detected or state.final_output is not None:
            return END
        return "analyze_image_and_query"

    def route_after_analysis(state: AgentState):
        if not state.is_image_usable or state.final_output is not None:
            return END
        return "retrieve_sources"

    workflow.add_conditional_edges("verify_access", route_after_access)
    workflow.add_conditional_edges("analyze_image_and_query", route_after_analysis)
    workflow.add_edge("retrieve_sources", "rerank_sources")
    workflow.add_edge("rerank_sources", "consult_mcp_history")
    workflow.add_edge("consult_mcp_history", "synthesize_and_verify")

    # Branche après synthèse : Si validation humaine demandée et déjà approuvée
    def route_after_synthesis(state: AgentState):
        if state.draft_action and state.human_approved:
            return "execute_mcp_action"
        return END

    workflow.add_conditional_edges("synthesize_and_verify", route_after_synthesis)
    workflow.add_edge("execute_mcp_action", END)

    return workflow.compile()

# Instance du graphe compilé
agent_graph = build_autoclaim_graph()
