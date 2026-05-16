"""LangGraph workflow for scope change detection."""
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from backend.agent.nodes.retrieve import retrieve_baseline_context
from backend.agent.nodes.extract import extract_scope_change
from backend.agent.nodes.diff import diff_against_baseline, validate_extraction
from backend.agent.nodes.route import route_change, should_auto_approve, should_flag_for_pm, should_ignore


class AgentState(TypedDict):
    """State for the scope change detection agent."""
    project_id: str
    message: str
    sender: str
    source: str
    date: str
    routing_status: str
    baseline: dict
    extracted: dict
    diffed: dict
    routing_decision: dict
    final_action: str
    errors: list[str]


def retrieve_node(state: AgentState) -> AgentState:
    """Retrieve baseline context for the project."""
    baseline = retrieve_baseline_context(state["project_id"])
    state["baseline"] = baseline
    return state


def extract_node(state: AgentState) -> AgentState:
    """Extract scope change from message using LLM."""
    extracted = extract_scope_change(
        message=state["message"],
        baseline=state["baseline"],
        sender=state.get("sender", "unknown"),
        source=state.get("source", "email"),
        date=state.get("date", "")
    )
    state["extracted"] = extracted
    return state


def diff_node(state: AgentState) -> AgentState:
    """Compare extracted data against baseline."""
    # Validate extraction first
    is_valid, errors = validate_extraction(state["extracted"])
    
    if not is_valid:
        state["errors"] = errors
        # Set a safe default for invalid extractions
        state["diffed"] = state["extracted"].copy()
        state["diffed"]["validation_errors"] = errors
        return state
    
    # Perform diff
    diffed = diff_against_baseline(state["extracted"], state["baseline"])
    state["diffed"] = diffed
    state["errors"] = []
    return state


def risk_node(state: AgentState) -> AgentState:
    """Apply risk rules to determine routing."""
    routing_decision = route_change(
        state["diffed"],
        routing_status=state.get("routing_status", "resolved")
    )
    state["routing_decision"] = routing_decision
    state["final_action"] = routing_decision["final_action"]
    return state


def route_node(state: AgentState) -> str:
    """Determine next step based on final action."""
    final_action = state.get("final_action", "flag_for_pm")
    
    if final_action == "auto_approve":
        return "auto_approve"
    elif final_action == "ignore":
        return "ignore"
    else:
        return "flag_for_pm"


def build_graph() -> StateGraph:
    """
    Build the LangGraph workflow for scope change detection.
    
    Workflow:
    1. retrieve: Get baseline context from database
    2. extract: Use LLM to extract scope change info
    3. diff: Compare against baseline and validate
    4. risk: Apply risk rules
    5. route: Determine final action
    
    Returns:
        Compiled StateGraph
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("extract", extract_node)
    workflow.add_node("diff", diff_node)
    workflow.add_node("risk", risk_node)
    
    # Define edges
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "extract")
    workflow.add_edge("extract", "diff")
    workflow.add_edge("diff", "risk")
    
    # Conditional routing from risk node
    workflow.add_conditional_edges(
        "risk",
        route_node,
        {
            "auto_approve": END,
            "flag_for_pm": END,
            "ignore": END
        }
    )
    
    return workflow.compile()


def run_scope_change_detection(
    project_id: str,
    message: str,
    sender: str = "unknown",
    source: str = "email",
    date: str = "",
    routing_status: str = "resolved"
) -> dict:
    """
    Run the scope change detection workflow.
    
    Args:
        project_id: UUID of the project
        message: Client message text
        sender: Message sender
        source: Message source (email, slack, etc.)
        date: Message date
        routing_status: Project routing status
        
    Returns:
        Final state with routing decision
    """
    graph = build_graph()
    
    initial_state: AgentState = {
        "project_id": project_id,
        "message": message,
        "sender": sender,
        "source": source,
        "date": date,
        "routing_status": routing_status,
        "baseline": {},
        "extracted": {},
        "diffed": {},
        "routing_decision": {},
        "final_action": "",
        "errors": []
    }
    
    # Run the graph
    final_state = graph.invoke(initial_state)
    
    return final_state

# Made with Bob
