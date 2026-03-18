# Assignment 4 Grading Review

**Status:** 🚨 CRITICAL ISSUES FOUND - See Below

---

## ✅ What's Working

### 1. Project Structure ✅
- [x] `.gitignore` exists with `.env` exclusion
- [x] `requirements.txt` includes `python-dotenv`, `langgraph`, `langchain-openai`
- [x] `README.md` documents `python app.py` and warns about `.env` not being committed
- [x] `prompts/supervisor_v1.yaml` exists with all required fields

### 2. MultiAgentState TypedDict ✅
```python
class MultiAgentState(TypedDict):
    user_request: str           ✅
    route: str                  ✅
    agent_used: str             ✅
    specialist_result: str      ✅
    final_response: str         ✅
```
All 5 required keys present.

### 3. YAML Loading ✅
- [x] `load_supervisor_prompt()` loads from `prompts/supervisor_v1.yaml`
- [x] Uses `yaml.safe_load()`
- [x] YAML contains all required fields (version, name, created_by, created_at, description, changelog, system)

### 4. Supervisor Node ✅
- [x] `supervisor_node()` classifies request
- [x] Loads YAML prompt dynamically
- [x] Returns normalized route validated against VALID_ROUTES
- [x] Calls LLM with SystemMessage from YAML

### 5. Routing Function ✅
```python
def route_to_specialist(state: MultiAgentState) -> str:
    route_mapping = {
        "orders": "orders_agent",
        "billing": "billing_agent",
        "technical": "technical_agent",
        "subscription": "subscription_agent",
        "general": "general_agent"
    }
    return route_mapping.get(state["route"], "general_agent")
```
Maps all 5 categories correctly ✅

### 6. LangGraph Structure ✅
- [x] Uses `StateGraph(MultiAgentState)`
- [x] Uses `add_conditional_edges()`
- [x] Entry point set to supervisor
- [x] All specialists connect to synthesize node
- [x] Synthesize connects to END

### 7. Specialist Agents ✅
- [x] `orders_agent_node` exists
- [x] `billing_agent_node` exists
- [x] `technical_agent_node` exists
- [x] `subscription_agent_node` exists
- [x] `general_agent_node` exists (fallback)
- [x] Each writes `agent_used` and `specialist_result`

### 8. AgentHandoff Dataclass ✅
```python
@dataclass
class AgentHandoff:
    from_agent: str
    to_agent: str
    context: str
    metadata: dict = field(default_factory=dict)
```
Dataclass defined with required fields.

### 9. Injection Detection ✅
- [x] `detect_injection()` function exists
- [x] `guard_request()` function exists
- [x] INJECTION_PATTERNS defined
- [x] Called in `main()` before graph invocation

### 10. SessionAuditLog ✅
```python
@dataclass
class SessionAuditLog:
    session_id: str
    events: list = field(default_factory=list)
    total_cost_usd: float = 0.0
    
    def log(self, event: dict):  ✅
        ...
    
    def add_cost(self, agent: str, input_tokens: int, output_tokens: int):
        ...
```
Has `log()` method and `total_cost_usd` field.

### 11. Audit Persistence ✅
- [x] `persist_audit_log()` function exists
- [x] Writes to `audit_log.jsonl`
- [x] Appends JSONL format (one JSON object per line)

### 12. main() Execution ✅
- [x] Creates `SessionAuditLog`
- [x] Builds graph
- [x] Runs 2+ test requests
- [x] Prints route and agent_used
- [x] Prints final_response
- [x] Displays total cost

---

## 🚨 CRITICAL ISSUES TO FIX

### Issue 1: DUPLICATE main() FUNCTION ⚠️ CRITICAL
**File:** `app.py`  
**Lines:** There are TWO `main()` functions!
- First `main()`: Lines 486-550 (correct implementation) ✅
- Second `main()`: Lines 552-704 (skeleton/placeholder) ❌

**Problem:** Python will use the SECOND definition (lines 552-704), which is just a placeholder that prints development notes. The grader will run the PLACEHOLDER version, not the correct implementation.

**Fix Required:** DELETE lines 552-704 (the entire skeleton main() function)

**Severity:** 🔴 CRITICAL - This will cause the grader to fail completely

---

### Issue 2: guard_request() Return Type Mismatch ⚠️ HIGH
**File:** `app.py`, Lines 128-134  
**Current:**
```python
def guard_request(request: str) -> tuple[bool, Optional[str]]:
    """Guard against injection attacks. Returns (is_safe, error_message)."""
    if detect_injection(request):
        error = "Injection detected. Request blocked."
        return False, error
    return True, None
```

**Problem:** 
1. Function returns `tuple[bool, Optional[str]]`
2. But in `main()` (lines 512-516), it's called as if returning `tuple`:
```python
is_safe, error = guard_request(request)
if not is_safe:
    logger.error(error)
    continue
```

3. The assignment example expects it to return a `str`:
```python
def guard_request(user_input: str) -> str:
    if detect_injection(user_input):
        return "I can only assist with account and order support. (Request blocked.)"
    return user_input
```

**Fix Required:** Change `guard_request()` to match assignment spec:
```python
def guard_request(request: str) -> str:
    """Guard against injection attacks. Returns safe request or error message."""
    if detect_injection(request):
        return "[SECURITY] Request blocked due to injection attempt."
    return request
```

Then update the call in `main()`:
```python
safe_request = guard_request(request)
if safe_request != request:  # Injection detected
    logger.error(safe_request)
    continue

# Use safe_request for state
initial_state = MultiAgentState(
    user_request=safe_request,
    ...
)
```

**Severity:** 🟠 HIGH - May cause type checking to fail in grader

---

### Issue 3: AgentHandoff is Defined but NOT USED ⚠️ MEDIUM
**File:** `app.py`, Lines 75-81  
**Current:**
```python
@dataclass
class AgentHandoff:
    """Structured handoff between agents."""
    from_agent: str
    to_agent: str
    context: str
    metadata: dict = field(default_factory=dict)
```

**Problem:** 
The dataclass is defined but never instantiated or used anywhere in the code.  
Assignment requirement says: "Use this pattern at least once, for example when the supervisor calls a specialist"

**Fix Required:** 
Instantiate `AgentHandoff` in one of the specialist nodes to demonstrate structured handoffs.

Example in `supervisor_node()` or specialist nodes:
```python
def orders_agent_node(state: MultiAgentState, audit: SessionAuditLog) -> MultiAgentState:
    """Orders specialist agent."""
    
    # Create a structured handoff
    handoff = AgentHandoff(
        from_agent="supervisor",
        to_agent="orders_agent",
        context=state["user_request"],
        metadata={"route": state["route"]}
    )
    logger.info(f"[HANDOFF] {handoff.from_agent} -> {handoff.to_agent}")
    
    # ... rest of implementation
```

**Severity:** 🟡 MEDIUM - Grader checks for AgentHandoff existence; may check usage too

---

### Issue 4: Overly Strict Injection Patterns ⚠️ MEDIUM
**File:** `app.py`, Lines 49-54  
**Current Patterns:**
```python
INJECTION_PATTERNS = [
    r"(\b(DROP|DELETE|UPDATE|INSERT|CREATE|ALTER|TRUNCATE|EXEC|EXECUTE)\b)",  # SQL injection
    r"(\bscript\b.*\bon\w+\b)",  # JavaScript injection
    r"(\$\{.*?\})",  # Template injection
    r"(\.\.\/)",  # Path traversal
]
```

**Problem:**
These patterns are SQL/JavaScript focused, not prompt injection focused.  
The test requests will likely NOT match these patterns, which is good.  
However, the patterns don't match the assignment examples like:
- "ignore your instructions"
- "system prompt disabled"
- "you are now a"
- "repeat system prompt"
- "jailbreak"

**Risk:** If grader tests with prompt injection examples, they won't be caught.

**Fix:** Replace with patterns from assignment:
```python
INJECTION_PATTERNS: Final[list[str]] = [
    r"ignore (your |all |previous )?instructions",
    r"system prompt.*disabled",
    r"you are now a",
    r"repeat.*system prompt",
    r"jailbreak",
]
```

**Severity:** 🟡 MEDIUM - May fail specific injection test cases

---

### Issue 5: Message History Not Explicit ⚠️ MEDIUM (From Feedback)
**Context:** User mentioned "Improve: make your Reflection sharper + keep message history explicit" as feedback from others' reviews.

**Current State:** 
- No explicit message history management
- Each agent node creates fresh LLM calls
- No conversation context carried between nodes

**Note:** This may NOT be required for this assignment, but it was mentioned in feedback.

**Recommendation:** Optional - Add message history tracking:
```python
@dataclass
class SessionAuditLog:
    session_id: str
    events: list = field(default_factory=list)
    total_cost_usd: float = 0.0
    message_history: list = field(default_factory=list)  # Add this
    
    def add_message(self, agent: str, role: str, content: str):
        self.message_history.append({
            "agent": agent,
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
```

**Severity:** 🟢 LOW - Probably not required but mentioned in feedback

---

## Summary of Required Fixes

| Issue | Severity | Fix | Time |
|-------|----------|-----|------|
| Duplicate main() | 🔴 CRITICAL | Delete skeleton main() (lines 552-704) | 2 min |
| guard_request() signature | 🟠 HIGH | Change return type and update calls | 5 min |
| AgentHandoff unused | 🟡 MEDIUM | Instantiate in a node | 3 min |
| Injection patterns | 🟡 MEDIUM | Use assignment's patterns | 2 min |
| Message history | 🟢 LOW | Optional enhancement | 10 min |

**Total Fix Time:** ~12 minutes for critical + high issues

---

## Grading Criteria Checklist

- [x] Project contract (`.env` ignored, requirements correct, README updated)
- [x] MultiAgentState (5 required keys)
- [x] Supervisor + routing (YAML loaded, supervisor_node, route_to_specialist)
- [x] Graph structure (StateGraph, add_conditional_edges, all nodes)
- [x] Specialist agents (4 specialists + general)
- [x] AgentHandoff dataclass exists (but NOT used - needs fix)
- [x] Injection detection (detect_injection exists, but patterns weak)
- [x] SessionAuditLog (with log method and total_cost_usd)
- [x] persist_audit_log function (writes JSONL)
- [x] main() (runs 2+ requests - but currently unused due to duplicate)

---

## Expected Grading Score

**Before fixes:** ~60-70% (fails on critical/high issues)  
**After fixes:** ~95-100% (all requirements met)

---

## Recommendations for 100% Score

1. **MUST DO:** Delete duplicate main() function immediately
2. **MUST DO:** Fix guard_request() signature to match assignment
3. **SHOULD DO:** Actually use AgentHandoff in code
4. **SHOULD DO:** Use assignment's injection patterns
5. **NICE TO HAVE:** Add message history tracking to SessionAuditLog

