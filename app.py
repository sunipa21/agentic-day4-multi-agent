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
import sys
import re
import json
import logging
from typing import TypedDict, Literal, Final, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import yaml
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
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

# Injection pattern detection
INJECTION_PATTERNS = [
    r"(\b(DROP|DELETE|UPDATE|INSERT|CREATE|ALTER|TRUNCATE|EXEC|EXECUTE)\b)",  # SQL injection
    r"(\bscript\b.*\bon\w+\b)",  # JavaScript injection
    r"(\$\{.*?\})",  # Template injection
    r"(\.\.\/)",  # Path traversal
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
    context: str
    metadata: dict = field(default_factory=dict)


@dataclass
class SessionAuditLog:
    """Session-level audit log with cost tracking."""

    session_id: str
    events: list = field(default_factory=list)
    total_cost_usd: float = 0.0

    def log(self, event: dict):
        """Log an event and update cost."""
        self.events.append({"timestamp": datetime.now().isoformat(), **event})

    def add_cost(self, agent: str, input_tokens: int, output_tokens: int):
        """Add cost for an agent call (mocked pricing)."""
        # Mocked pricing: $0.0001 per token
        cost = (input_tokens + output_tokens) * 0.000001
        self.total_cost_usd += cost
        self.log(
            {
                "agent": agent,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost,
            }
        )


# ============================================================================
# INJECTION DETECTION
# ============================================================================


def detect_injection(text: str) -> bool:
    """Detect potential injection attacks in user input."""
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def guard_request(request: str) -> tuple[bool, Optional[str]]:
    """Guard against injection attacks. Returns (is_safe, error_message)."""
    if detect_injection(request):
        error = f"[SECURITY] Injection detected. Request blocked."
        logger.warning(f"Injection attempt detected in request: {request[:100]}")
        return False, error
    return True, None


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


def supervisor_node(state: MultiAgentState, audit: SessionAuditLog) -> MultiAgentState:
    """Supervisor node: Classify request and route to appropriate specialist."""
    logger.info(f"[SUPERVISOR] Processing: {state['user_request'][:50]}...")

    llm = get_llm()
    supervisor_prompt = load_supervisor_prompt()

    # Create messages for supervisor
    system_msg = SystemMessage(content=supervisor_prompt)
    human_msg = HumanMessage(content=f"Classify this request: {state['user_request']}")

    # Get classification
    response = llm.invoke([system_msg, human_msg])
    classification = response.content.strip().lower()

    # Validate classification
    if classification not in VALID_ROUTES:
        classification = "general"

    # Log and update cost
    audit.add_cost(
        "supervisor",
        input_tokens=PRICING["supervisor"]["input_tokens"],
        output_tokens=PRICING["supervisor"]["output_tokens"],
    )

    logger.info(f"[SUPERVISOR] Classified as: {classification}")

    state["route"] = classification
    return state


def orders_agent_node(
    state: MultiAgentState, audit: SessionAuditLog
) -> MultiAgentState:
    """Orders specialist agent."""
    logger.info(f"[ORDERS AGENT] Handling: {state['user_request'][:50]}...")

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

    audit.add_cost(
        "specialist",
        input_tokens=PRICING["specialist"]["input_tokens"],
        output_tokens=PRICING["specialist"]["output_tokens"],
    )

    state["agent_used"] = "orders_agent"
    state["specialist_result"] = response.content
    return state


def billing_agent_node(
    state: MultiAgentState, audit: SessionAuditLog
) -> MultiAgentState:
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

    audit.add_cost(
        "specialist",
        input_tokens=PRICING["specialist"]["input_tokens"],
        output_tokens=PRICING["specialist"]["output_tokens"],
    )

    state["agent_used"] = "billing_agent"
    state["specialist_result"] = response.content
    return state


def technical_agent_node(
    state: MultiAgentState, audit: SessionAuditLog
) -> MultiAgentState:
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

    audit.add_cost(
        "specialist",
        input_tokens=PRICING["specialist"]["input_tokens"],
        output_tokens=PRICING["specialist"]["output_tokens"],
    )

    state["agent_used"] = "technical_agent"
    state["specialist_result"] = response.content
    return state


def subscription_agent_node(
    state: MultiAgentState, audit: SessionAuditLog
) -> MultiAgentState:
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

    audit.add_cost(
        "specialist",
        input_tokens=PRICING["specialist"]["input_tokens"],
        output_tokens=PRICING["specialist"]["output_tokens"],
    )

    state["agent_used"] = "subscription_agent"
    state["specialist_result"] = response.content
    return state


def general_agent_node(
    state: MultiAgentState, audit: SessionAuditLog
) -> MultiAgentState:
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

    audit.add_cost(
        "specialist",
        input_tokens=PRICING["specialist"]["input_tokens"],
        output_tokens=PRICING["specialist"]["output_tokens"],
    )

    state["agent_used"] = "general_agent"
    state["specialist_result"] = response.content
    return state


def synthesize_response_node(
    state: MultiAgentState, audit: SessionAuditLog
) -> MultiAgentState:
    """Synthesize final response from specialist result."""
    logger.info("[SYNTHESIZER] Creating final response...")

    # Format final response
    final_response = f"""
[Customer Support Response]
Routed to: {state["agent_used"]}
Response: {state["specialist_result"]}
"""

    state["final_response"] = final_response
    return state


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


def persist_audit_log(audit: SessionAuditLog):
    """Persist audit log to JSONL file."""
    log_file = Path(__file__).parent / "audit_log.jsonl"

    try:
        audit_dict = {
            "session_id": audit.session_id,
            "timestamp": datetime.now().isoformat(),
            "total_cost_usd": audit.total_cost_usd,
            "event_count": len(audit.events),
            "events": audit.events,
        }

        with open(log_file, "a") as f:
            f.write(json.dumps(audit_dict) + "\n")

        logger.info(f"Audit log persisted to {log_file}")
    except Exception as e:
        logger.error(f"Error persisting audit log: {e}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main():
    """Main entry point demonstrating the multi-agent system."""
    logger.info("=" * 70)
    logger.info("Multi-Agent Customer Support System")
    logger.info("=" * 70)

    # Create audit session
    session_id = str(uuid4())
    audit = SessionAuditLog(session_id=session_id)

    # Build graph
    graph = build_graph(audit)

    # Example requests
    test_requests = [
        "I need to track my recent order #12345",
        "There's an error when I try to login to my account",
    ]

    for i, request in enumerate(test_requests, 1):
        logger.info(f"\n[TEST {i}] Request: {request}")

        # Check for injection
        is_safe, error = guard_request(request)
        if not is_safe:
            logger.error(error)
            continue

        # Initialize state
        initial_state = MultiAgentState(
            user_request=request,
            route="",
            agent_used="",
            specialist_result="",
            final_response="",
        )

        # Execute graph
        final_state = graph.invoke(initial_state)

        # Print results
        logger.info(f"[RESULT {i}] Route: {final_state['route']}")
        logger.info(f"[RESULT {i}] Agent: {final_state['agent_used']}")
        logger.info(f"[RESULT {i}] Response:\n{final_state['final_response']}")

    # Display audit summary
    logger.info("\n" + "=" * 70)
    logger.info("AUDIT SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Session ID: {audit.session_id}")
    logger.info(f"Total Events: {len(audit.events)}")
    logger.info(f"Total Cost: ${audit.total_cost_usd:.8f}")

    # Persist audit log
    persist_audit_log(audit)

    logger.info("\n✓ Multi-agent system execution complete!")


if __name__ == "__main__":
    main()


def main() -> None:
    """
    Main entry point for multi-agent system.

    This is the skeleton for the multi-agent application.
    Components will be implemented iteratively:

    Phase 1: Agent base classes
    Phase 2: Orchestrator framework
    Phase 3: Memory and state management
    Phase 4: Tool registry and integration
    Phase 5: Communication protocols
    Phase 6: Production monitoring
    """
    print("=" * 70)
    print(" MULTI-AGENT SYSTEM - DAY 4")
    print("=" * 70)

    print("\n📋 PROJECT STATUS")
    print("-" * 70)
    print("Status: In Development")
    print("Phase: 1 - Architecture Design")
    print("Created: March 19, 2026")
    print()

    print("🎯 COMPONENTS TO BUILD")
    print("-" * 70)
    components = [
        ("1. Agent Base Class", "Foundation for all agents"),
        ("2. Orchestrator", "Multi-agent coordination"),
        ("3. Memory System", "Shared state and knowledge"),
        ("4. Tool Registry", "Tool integration framework"),
        ("5. Communication", "Inter-agent messaging"),
        ("6. Monitoring", "Production observability"),
    ]

    for component, description in components:
        print(f"  ⏳ {component:30} - {description}")
    print()

    print("🏗️ PROJECT STRUCTURE")
    print("-" * 70)
    print("""
    agentic-day4-multi-agent/
    ├── app.py                  # Main application (this file)
    ├── agent_base.py           # Agent base class [TODO]
    ├── orchestrator.py         # Orchestrator [TODO]
    ├── memory.py               # Memory system [TODO]
    ├── tools.py                # Tool registry [TODO]
    ├── prompts/                # Agent prompts [TODO]
    ├── tests/                  # Test suite [TODO]
    └── examples/               # Examples [TODO]
    """)

    print("📚 KEY PATTERNS TO IMPLEMENT")
    print("-" * 70)
    patterns = [
        "Sequential Agent Execution",
        "Parallel Agent Execution",
        "Hierarchical Agent Organization",
        "Peer-to-Peer Agent Network",
        "Task Decomposition",
        "Consensus Mechanisms",
        "Conflict Resolution",
        "Dynamic Agent Selection",
    ]

    for i, pattern in enumerate(patterns, 1):
        print(f"  {i}. {pattern}")
    print()

    print("🧪 TESTING STRATEGY")
    print("-" * 70)
    print("""
    Test Coverage Target: 30+ tests
    ├── Unit Tests (15+)
    │   ├── Agent lifecycle
    │   ├── Task routing
    │   ├── Memory operations
    │   └── Tool execution
    ├── Integration Tests (10+)
    │   ├── Multi-agent workflows
    │   ├── Communication patterns
    │   └── Error scenarios
    └── Performance Tests (5+)
        ├── Latency
        ├── Throughput
        └── Resource usage
    """)

    print("📊 ARCHITECTURE LAYERS")
    print("-" * 70)
    layers = [
        ("Layer 1", "Task Validation", "Verify inputs and constraints"),
        ("Layer 2", "Agent Health", "Monitor agent status and capacity"),
        ("Layer 3", "Resource Management", "Budget and rate limiting"),
        ("Layer 4", "State Consistency", "Maintain coherent system state"),
        ("Layer 5", "Error Recovery", "Handle failures and recovery"),
        ("Layer 6", "Observability", "Logging, metrics, and monitoring"),
    ]

    for layer, name, description in layers:
        print(f"  {layer:10} {name:25} - {description}")
    print()

    print("🚀 NEXT STEPS")
    print("-" * 70)
    print("""
    1. Implement Agent base class
       - LLM integration
       - Tool access
       - State management
       - Error handling
    
    2. Build Orchestrator
       - Agent lifecycle management
       - Task routing logic
       - Communication framework
       - Consensus mechanisms
    
    3. Create Memory System
       - Shared state storage
       - Conversation history
       - Knowledge base
       - Vector storage
    
    4. Implement Tool Registry
       - Tool definitions
       - Tool execution
       - Error handling
       - Rate limiting
    
    5. Add monitoring and observability
    
    6. Write comprehensive tests
    """)

    print("=" * 70)
    print(" Ready to build! 🎯")
    print("=" * 70)
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
