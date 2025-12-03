# Orchestrator Routing Rules

## 🎯 Routing Logic: Orchestrator-First

The system uses an **Orchestrator-First** routing strategy. The Shared Orchestrator is **always** the first hop for every task. It analyzes the task domain and the customer's team composition to make an intelligent routing decision.

### 🧠 Core Routing Rules

The Orchestrator follows these prioritized rules:

1.  **Domain Analysis**: Identify the task's domain (e.g., Marketing, IT, HR, Sales).
2.  **Manager Preference**: IF a Manager exists **for that specific domain**, route to them.
3.  **Cross-Functional**: IF the task requires multiple departments, identify the primary department's manager or a "Lead" manager.
4.  **Specialist Fallback**: IF no manager exists for the domain, route to the most senior specialist in that domain.
5.  **Relevance**: IF multiple managers exist, route to the one most relevant to the core objective.

## 📊 Routing Decision Flow

```
Task Created
     ↓
Shared Orchestrator (Analyzes Task & Team)
     ↓
     ├─→ Marketing Task?
     │    ├─→ Marketing Manager Exists? → Route to Marketing Manager
     │    └─→ No Manager? → Route to Senior Marketing Specialist
     │
     ├─→ IT Task?
     │    ├─→ IT Manager Exists? → Route to IT Manager
     │    └─→ No Manager? → Route to Senior Developer
     │
     └─→ Cross-Functional?
          ├─→ Identify Primary Domain
          └─→ Route to Primary Manager (who delegates to others)
```

## 🔧 Implementation

### Backend: `orchestrator.py`

The Orchestrator receives the following context:

```python
context={
    "task_id": task_id,
    "routing_rules": [
        "1. ALWAYS analyze the task domain (e.g., Marketing, IT, Sales).",
        "2. IF a Manager exists for that domain, route to them.",
        "3. IF the task requires multiple departments, identify the primary department's manager.",
        "4. IF no manager exists for the domain, route to the most senior specialist.",
        "5. IF multiple managers are needed, route to the one most relevant to the core objective."
    ],
    "available_ves": [
        {
            "id": "...",
            "name": "Sarah",
            "role": "Marketing Manager",
            "department": "Marketing",
            "seniority": "manager"
        },
        # ... other agents
    ]
}
```

## 📝 Examples

### Example 1: Multiple Managers (Marketing & IT)

**Team:**
*   **Sarah** (Marketing Manager)
*   **Mike** (IT Manager)
*   **Jenny** (Content Creator)

**Task:** "Fix the server outage affecting the website."

**Routing:**
1.  Orchestrator identifies domain: **IT / Technical**.
2.  Checks for IT Manager.
3.  Finds **Mike**.
4.  **Routes to Mike**.

**Task:** "Launch a new email campaign for the summer sale."

**Routing:**
1.  Orchestrator identifies domain: **Marketing**.
2.  Checks for Marketing Manager.
3.  Finds **Sarah**.
4.  **Routes to Sarah**.

### Example 2: Cross-Functional Task

**Team:**
*   **Sarah** (Marketing Manager)
*   **Mike** (IT Manager)

**Task:** "Update the website homepage with the new summer sale banners."

**Routing:**
1.  Orchestrator identifies domains: **Marketing** (content) & **IT** (website update).
2.  Determines primary objective: **Marketing** (the sale).
3.  **Routes to Sarah** (Marketing Manager).
4.  *Note: Sarah may then delegate the technical implementation to Mike via A2A.*

### Example 3: No Manager for Domain

**Team:**
*   **Sarah** (Marketing Manager)
*   **Dave** (Junior Developer)

**Task:** "Fix a bug in the login form."

**Routing:**
1.  Orchestrator identifies domain: **IT**.
2.  Checks for IT Manager. **None found.**
3.  Checks for IT Specialists. Finds **Dave**.
4.  **Routes to Dave**.

## ✅ Benefits of This Approach

*   **Intelligent Routing**: Doesn't blindly send IT tasks to a Marketing Manager just because they are a "Manager".
*   **Scalability**: Handles complex organizations with multiple departments.
*   **Flexibility**: Works for flat structures (no managers) and hierarchical ones.
*   **Context Aware**: Understands the *content* of the task, not just the availability of agents.

---

**Status:** ✅ Implemented
**Strategy:** Orchestrator-First with Domain Awareness
**Date:** December 1, 2025
