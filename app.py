"""
Multi-Agent Customer Support System - Day 4 Assignment

Implements a production-ready multi-agent system with:
- Supervisor agent for classification and routing
- 4 specialist agents + general fallback
- Structured handoffs between agents
- Injection detection at entry point
- Session-level audit logging with cost tracking
- Complete LangGraph orchestration

Author: AI Architect
Created: March 19, 2026
"""

import os
import re
import json
import logging
from typing import TypedDict, Final
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

VALID_ROUTES = {"orders", "billing", "technical", "subscription", "general"}

# Prompt injection pattern detection (from assignment)
INJECTION_PATTERNS: Final[list[str]] = [
    r"ignore (your |all |previous )?instructions",
    r"system prompt.*disabled",
    r"you are now a",
    r"repeat.*system prompt",
    r"jailbreak",
]

# Token pricing per request (mocked for demo)
PRICING = {
    "supervisor": {"input_tokens": 50, "output_tokens": 5},
    "specialist": {"input_tokens": 100, "output_tokens": 50},
}

# ============================================================================
# TYPE DEFINITIONS
# ============================================================================


class MultiAgentState(TypedDict):
    """State shared across all agents in the graph."""

    user_request: str
    route: str
    agent_used: str
    specialist_result: str
    final_response: str


@dataclass
class AgentHandoff:
    """Structured handoff between agents."""

    from_agent: str
    to_agent: str
    task: str
    context: dict
    priority: str  # "low" | "normal" | "high"
    timestamp: str

    def to_prompt_context(self) -> str:
        return (
            f"HANDOFF FROM {self.from_agent.upper()} TO {self.to_agent.upper()}:\n"
            f"Task: {self.task}\n"
            f"Priority: {self.priority}\n"
            f"Context: {self.context}\n"
            f"Received at: {self.timestamp}"
        )


@dataclass
class SessionAuditLog:
    """Session-level audit log with cost tracking."""

    session_id: str
    events: list = field(default_factory=list)
    total_cost_usd: float = 0.0

    def log(
        self, agent: str, action: str, tokens_in: int = 0, tokens_out: int = 0
    ) -> None:
        """Log an event and update cost."""
        cost = (tokens_in * 0.000015 + tokens_out * 0.00006) / 1000
        self.total_cost_usd += cost
        self.events.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "agent": agent,
                "action": action,
                "cost_usd": round(cost, 6),
            }
        )

    def to_dict(self) -> dict:
        """Convert audit log to dictionary."""
        return {
            "session_id": self.session_id,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "events": self.events,
        }


# ============================================================================
# INJECTION DETECTION
# ============================================================================


def detect_injection(text: str) -> bool:
    """Detect potential injection attacks in user input."""
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def guard_request(request: str) -> str:
    """Guard against injection attacks. Returns safe request or error message."""
    if detect_injection(request):
        error_msg = (
            "I can only assist with account and order support. (Request blocked.)"
        )
        logger.warning(f"Injection attempt detected in request: {request[:100]}")
        return error_msg
    return request


# ============================================================================
# PROMPT LOADING
# ============================================================================


def load_supervisor_prompt() -> str:
    """Load supervisor prompt from YAML file."""
    yaml_path = Path(__file__).parent / "prompts" / "supervisor_v1.yaml"

    try:
        with open(yaml_path, "r") as f:
            config = yaml.safe_load(f)

        prompt = config.get("system", "")
        logger.info(f"Loaded supervisor prompt from {yaml_path}")
        return prompt

    except FileNotFoundError:
        logger.error(f"Supervisor YAML not found at {yaml_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading supervisor prompt: {e}")
        raise


# ============================================================================
# LLM INITIALIZATION
# ============================================================================


def get_llm() -> ChatOpenAI:
    """Initialize LLM with OpenAI API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")

    return ChatOpenAI(model="gpt-4o-mini", api_key=api_key, temperature=0.3)


# ============================================================================
# GRAPH NODES
# ============================================================================


def supervisor_node(state: MultiAgentState, audit: SessionAuditLog) -> dict:
    """Supervisor node: Classify request and route to appropriate specialist."""
    logger.info(f"[SUPERVISOR] Processing: {state['user_request'][:50]}...")

    llm = get_llm()
    supervisor_prompt = load_supervisor_prompt()

    # Create messages for supervisor
    messages = [
        SystemMessage(content=supervisor_prompt),
        HumanMessage(content=state["user_request"]),
    ]

    # Get classification
    response = llm.invoke(messages)
    route = response.content.strip().lower()

    # Validate classification
    if route not in VALID_ROUTES:
        route = "general"

    # Log supervisor action
    audit.log(
        agent="supervisor",
        action=f"classified as {route}",
        tokens_in=PRICING["supervisor"]["input_tokens"],
        tokens_out=PRICING["supervisor"]["output_tokens"],
    )

    logger.info(f"[SUPERVISOR] Classified as: {route}")

    return {"route": route}


def orders_agent_node(state: MultiAgentState, audit: SessionAuditLog) -> dict:
    """Orders specialist agent."""
    logger.info(f"[ORDERS AGENT] Handling: {state['user_request'][:50]}...")

    # Create a structured handoff from supervisor to this specialist
    handoff = AgentHandoff(
        from_agent="supervisor",
        to_agent="orders_agent",
        task=state["user_request"],
        context={"route": state["route"]},
        priority="normal",
        timestamp=datetime.utcnow().isoformat(),
    )
    logger.info(f"[HANDOFF] {handoff.to_prompt_context()}")

    llm = get_llm()
    system_prompt = """You are an orders specialist agent. Handle inquiries about:
    - Order status and tracking
    - Order modifications
    - Returns and refunds
    - Order history
    
    Provide concise, helpful responses."""

    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state["user_request"]),
        ]
    )

    audit.log(
        agent="orders_agent",
        action="handled order request",
        tokens_in=PRICING["specialist"]["input_tokens"],
        tokens_out=PRICING["specialist"]["output_tokens"],
    )

    return {
        "agent_used": "orders_agent",
        "specialist_result": response.content,
    }


def billing_agent_node(state: MultiAgentState, audit: SessionAuditLog) -> dict:
    """Billing specialist agent."""
    logger.info(f"[BILLING AGENT] Handling: {state['user_request'][:50]}...")

    llm = get_llm()
    system_prompt = """You are a billing specialist agent. Handle inquiries about:
    - Invoices and payments
    - Billing disputes
    - Subscription costs
    - Payment methods
    
    Provide clear, helpful billing information."""

    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state["user_request"]),
        ]
    )

    audit.log(
        agent="billing_agent",
        action="handled billing request",
        tokens_in=PRICING["specialist"]["input_tokens"],
        tokens_out=PRICING["specialist"]["output_tokens"],
    )

    return {
        "agent_used": "billing_agent",
        "specialist_result": response.content,
    }


def technical_agent_node(state: MultiAgentState, audit: SessionAuditLog) -> dict:
    """Technical support specialist agent."""
    logger.info(f"[TECHNICAL AGENT] Handling: {state['user_request'][:50]}...")

    llm = get_llm()
    system_prompt = """You are a technical support specialist. Handle inquiries about:
    - Technical issues and troubleshooting
    - System errors and bugs
    - API/integration problems
    - Performance issues
    
    Provide clear troubleshooting steps."""

    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state["user_request"]),
        ]
    )

    audit.log(
        agent="technical_agent",
        action="handled technical request",
        tokens_in=PRICING["specialist"]["input_tokens"],
        tokens_out=PRICING["specialist"]["output_tokens"],
    )

    return {
        "agent_used": "technical_agent",
        "specialist_result": response.content,
    }


def subscription_agent_node(state: MultiAgentState, audit: SessionAuditLog) -> dict:
    """Subscription specialist agent."""
    logger.info(f"[SUBSCRIPTION AGENT] Handling: {state['user_request'][:50]}...")

    llm = get_llm()
    system_prompt = """You are a subscription specialist agent. Handle inquiries about:
    - Subscription plans and upgrades
    - Cancellations and downgrades
    - Billing cycles
    - Discount codes and promotions
    
    Provide helpful subscription guidance."""

    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state["user_request"]),
        ]
    )

    audit.log(
        agent="subscription_agent",
        action="handled subscription request",
        tokens_in=PRICING["specialist"]["input_tokens"],
        tokens_out=PRICING["specialist"]["output_tokens"],
    )

    return {
        "agent_used": "subscription_agent",
        "specialist_result": response.content,
    }


def general_agent_node(state: MultiAgentState, audit: SessionAuditLog) -> dict:
    """General fallback agent for unclassified requests."""
    logger.info(f"[GENERAL AGENT] Handling: {state['user_request'][:50]}...")

    llm = get_llm()
    system_prompt = """You are a general customer support agent. Handle miscellaneous inquiries
    that don't fit specific categories. Be helpful and professional."""

    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state["user_request"]),
        ]
    )

    audit.log(
        agent="general_agent",
        action="handled general request",
        tokens_in=PRICING["specialist"]["input_tokens"],
        tokens_out=PRICING["specialist"]["output_tokens"],
    )

    return {
        "agent_used": "general_agent",
        "specialist_result": response.content,
    }


def synthesize_response_node(state: MultiAgentState, audit: SessionAuditLog) -> dict:
    """Synthesize final response from specialist result."""
    logger.info("[SYNTHESIZER] Creating final response...")

    # Format final response
    final_response = (
        f"[Customer Support Response]\n"
        f"Routed to: {state['agent_used']}\n"
        f"Response: {state['specialist_result']}"
    )

    return {"final_response": final_response}


# ============================================================================
# ROUTING LOGIC
# ============================================================================


def route_to_specialist(state: MultiAgentState) -> str:
    """Route to appropriate specialist based on classification."""
    route_mapping = {
        "orders": "orders_agent",
        "billing": "billing_agent",
        "technical": "technical_agent",
        "subscription": "subscription_agent",
        "general": "general_agent",
    }
    return route_mapping.get(state["route"], "general_agent")


# ============================================================================
# GRAPH BUILDING
# ============================================================================


def build_graph(audit: SessionAuditLog):
    """Build the multi-agent graph."""
    graph = StateGraph(MultiAgentState)

    # Add nodes
    graph.add_node("supervisor", lambda state: supervisor_node(state, audit))
    graph.add_node("orders_agent", lambda state: orders_agent_node(state, audit))
    graph.add_node("billing_agent", lambda state: billing_agent_node(state, audit))
    graph.add_node("technical_agent", lambda state: technical_agent_node(state, audit))
    graph.add_node(
        "subscription_agent", lambda state: subscription_agent_node(state, audit)
    )
    graph.add_node("general_agent", lambda state: general_agent_node(state, audit))
    graph.add_node("synthesize", lambda state: synthesize_response_node(state, audit))

    # Add edges
    graph.set_entry_point("supervisor")

    # Conditional edge from supervisor to specialists
    graph.add_conditional_edges(
        "supervisor",
        route_to_specialist,
        {
            "orders_agent": "orders_agent",
            "billing_agent": "billing_agent",
            "technical_agent": "technical_agent",
            "subscription_agent": "subscription_agent",
            "general_agent": "general_agent",
        },
    )

    # All specialists connect to synthesize
    for agent in [
        "orders_agent",
        "billing_agent",
        "technical_agent",
        "subscription_agent",
        "general_agent",
    ]:
        graph.add_edge(agent, "synthesize")

    # Synthesize connects to end
    graph.add_edge("synthesize", END)

    return graph.compile()


# ============================================================================
# AUDIT LOGGING
# ============================================================================


def persist_audit_log(audit: SessionAuditLog) -> None:
    """Persist audit log to JSONL file."""
    path = Path("audit_log.jsonl")

    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(audit.to_dict()) + "\n")

        logger.info(f"Audit log persisted to {path}")
    except Exception as e:
        logger.error(f"Error persisting audit log: {e}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main() -> None:
    """Main entry point demonstrating the multi-agent system."""
    logger.info("=" * 70)
    logger.info("Multi-Agent Customer Support System")
    logger.info("=" * 70)

    # Create audit session
    audit = SessionAuditLog(session_id="demo-session")

    # Build graph
    graph = build_graph(audit)

    # Example requests (one orders, one subscription per assignment requirement)
    test_requests = [
        "My order ORD-123 is late, can I return it?",
        "I want to upgrade from Basic to Pro. What will it cost?",
    ]

    for request in test_requests:
        # Check for injection before invoking graph
        safe_text = guard_request(request)
        if safe_text != request:
            print(f"Request: {request}")
            print(f"Blocked: {safe_text}")
            print("---")
            continue

        # Initialize state
        state: MultiAgentState = {
            "user_request": safe_text,
            "route": "general",
            "agent_used": "",
            "specialist_result": "",
            "final_response": "",
        }

        # Execute graph
        result = graph.invoke(state)

        # Print results to stdout
        print("Request:", request)
        print("Route:", result.get("route"), "Agent used:", result.get("agent_used"))
        print("Final:", result.get("final_response"))
        print("---")

    # Print total cost
    print("Total cost (USD):", round(audit.total_cost_usd, 6))

    # Persist audit log
    persist_audit_log(audit)

    logger.info("\n✓ Multi-agent system execution complete!")


if __name__ == "__main__":
    main()
