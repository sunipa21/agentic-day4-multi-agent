# Agentic Day 4: Multi-Agent Collaboration – Supervisor + Specialists

**Production-Ready Multi-Agent Customer Support System**

## 📋 Overview

This project implements a **multi-agent customer support system** using LangGraph with:

- **Supervisor Agent** that classifies and routes requests
- **Specialist Agents** for 4 domains (orders, billing, technical, subscription)
- **Structured Handoffs** between agents (dataclass-based)
- **Graceful Degradation** with general fallback
- **Session-Level Audit Logging** with cost tracking
- **Injection Detection** at graph entry point

### Key Features
- ✅ Multi-agent orchestration using LangGraph
- ✅ Supervisor classification with YAML prompts
- ✅ Specialist routing to domain experts
- ✅ Typed state management (TypedDict)
- ✅ Structured agent handoffs (dataclass)
- ✅ Injection detection and blocking
- ✅ Complete audit logging with costs
- ✅ Production-ready error handling

## 🏗️ Architecture

```
Multi-Agent System
├── Entry Guard (Injection Detection)
├── Supervisor Agent (Classification & Routing)
├── Specialist Agents
│   ├── Orders Agent
│   ├── Billing Agent
│   ├── Technical Agent
│   ├── Subscription Agent
│   └── General Agent (fallback)
├── Structured Handoffs (AgentHandoff dataclass)
├── Synthesize Response Node
└── Audit & Cost Tracking
```

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/sunipa21/agentic-day4-multi-agent.git
cd agentic-day4-multi-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (IMPORTANT: .env must NOT be committed)
echo "OPENAI_API_KEY=your_key_here" > .env

# Run the application
python app.py
```

**⚠️ WARNING:** Do NOT commit `.env` file. It contains sensitive API keys.

## 📂 Project Structure

```
agentic-day4-multi-agent/
├── README.md                    # This file
├── requirements.txt             # Project dependencies
├── .gitignore                   # Git ignore (excludes .env)
├── app.py                       # Main application (multi-agent system)
├── prompts/
│   └── supervisor_v1.yaml       # Supervisor classification prompt
└── audit_log.jsonl              # Session audit logs (auto-generated)
```

## 🧩 Core Components

### 1. MultiAgentState (TypedDict)
Shared state across all nodes:
- `user_request` - Original user message
- `route` - Classified category (orders|billing|technical|subscription|general)
- `agent_used` - Which specialist handled it
- `specialist_result` - Raw output from specialist
- `final_response` - Final response to user

### 2. Supervisor Agent
- Classifies requests into 5 categories
- Uses YAML prompt for classification
- Routes to appropriate specialist

### 3. Specialist Agents
- **Orders Agent** - Returns, tracking, late deliveries
- **Billing Agent** - Payments, refunds, invoices
- **Technical Agent** - Bugs, errors, login issues
- **Subscription Agent** - Plan changes, pricing
- **General Agent** - Everything else

### 4. Structured Handoffs
`AgentHandoff` dataclass ensures type-safe, auditable transfers:
```python
@dataclass
class AgentHandoff:
    from_agent: str
    to_agent: str
    task: str
    context: dict
    priority: str
    timestamp: str
```

### 5. Injection Detection
Blocks prompt injection attempts at graph entry:
- Pattern matching for common jailbreak techniques
- Guard request before supervisor invocation

### 6. Audit Logging
Session-level tracking with:
- Event timestamps
- Agent actions
- Token usage (mocked)
- Cost calculation per call

## 🧪 How It Works

### Execution Flow

1. **Input Guard** - Detect injection attempts
2. **Supervisor Classification** - Route to category
3. **Specialist Handling** - Domain-specific processing
4. **Response Synthesis** - Format final response
5. **Audit Logging** - Track session and costs

### Example Run

```
Request: "My order ORD-123 is late, can I return it?"

Route:        orders
Agent Used:   orders_agent
Final:        [orders_agent] Handling request: My order ORD-123 is late...
Cost:         $0.000045

---

Request: "I want to upgrade from Basic to Pro. What will it cost?"

Route:        subscription
Agent Used:   subscription_agent
Final:        [subscription_agent] Handling request: I want to upgrade...
Cost:         $0.000045

Total Session Cost: $0.00009
```

## 📊 Production Readiness

Implements 6 hardening layers (from Day 3):

1. **Input Validation** - Injection detection
2. **Agent Health** - Routing success tracking
3. **Resource Management** - Cost tracking
4. **State Consistency** - TypedDict validation
5. **Error Recovery** - General fallback path
6. **Observability** - Complete audit logging

## 🔗 Dependencies

- **LangGraph** - Multi-agent orchestration
- **LangChain** - LLM integration
- **Pydantic** - Type validation
- **python-dotenv** - Environment variables
- **PyYAML** - Prompt configuration

## 📈 Performance Targets

- Route classification: < 1 second
- Specialist response: < 2 seconds
- Total request latency: < 5 seconds
- Cost per request: $0.00004 - $0.00006

## 🔐 Security

- ✅ Injection detection at entry
- ✅ No API keys in git (`.env` excluded)
- ✅ Typed state prevents injection
- ✅ Audit logging for compliance

## 🤝 Contributing

This is an educational project. Improvements welcome:
- Add more specialist agents
- Implement tool integration
- Improve cost tracking accuracy
- Add metrics and monitoring
- Expand test coverage

## 📝 License

Educational use only

## 📧 Questions?

Create an issue in this repository or check the assignment details.

---

**Status:** Production Ready ✅
**Phase:** Multi-Agent Collaboration
**Last Updated:** March 19, 2026
