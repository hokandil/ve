# VE SaaS Platform - Admin Creator Interface
## Building VEs, Tools, and MCP Servers

---

## Overview: Interfaces 


### 2. **Hybrid Studio (Low-Code)** - For technical admins
- Visual + YAML editing
- Live preview
- Template customization
- Import/export configs



---

## Interface 1: Visual Studio (Recommended for You!)

### VE Creation Wizard

**Access:** Admin Dashboard → "Create New VE" → Choose: Visual Builder

```
┌─────────────────────────────────────────────────────────┐
│  Create New Virtual Employee                           │
│  Step 1 of 6: Basic Information                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  VE Name:                                              │
│  [Customer Success Manager                          ]  │
│                                                         │
│  Department:                                           │
│  [Customer Success ▼]                                  │
│   • Marketing                                          │
│   • Customer Support                                   │
│   • Sales                                              │
│   • Customer Success ✓                                 │
│   • Operations                                         │
│   • + Add Custom Department                            │
│                                                         │
│  Seniority Level:                                      │
│  ( ) Junior    ( ) Senior    (•) Manager              │
│                                                         │
│  Default Persona Name:                                 │
│  [Rachel Thompson                                   ]  │
│                                                         │
│  Short Description (shown in marketplace):             │
│  ┌─────────────────────────────────────────────────┐  │
│  │Manages customer success initiatives, ensures     │  │
│  │retention, and drives expansion revenue          │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  [Cancel]  [Back]  [Next: Define Personality →]       │
└─────────────────────────────────────────────────────────┘
```

**Step 2: Personality & Backstory**

```
┌─────────────────────────────────────────────────────────┐
│  Create New VE - Step 2 of 6: Personality              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Role Definition:                                      │
│  ┌─────────────────────────────────────────────────┐  │
│  │You are a Customer Success Manager responsible    │  │
│  │for ensuring customer satisfaction, retention,    │  │
│  │and growth. You proactively monitor customer     │  │
│  │health and intervene when needed.                │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Backstory (helps with decision-making):               │
│  ┌─────────────────────────────────────────────────┐  │
│  │You have 10 years of experience in B2B SaaS      │  │
│  │customer success. You believe in proactive       │  │
│  │outreach and data-driven decision making. You    │  │
│  │always put the customer first and focus on       │  │
│  │long-term relationships over quick wins.         │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Communication Style:                                  │
│  [Professional and Empathetic ▼]                       │
│   • Casual and Friendly                               │
│   • Professional and Empathetic ✓                     │
│   • Formal and Authoritative                          │
│   • Technical and Detailed                            │
│   • Custom...                                         │
│                                                         │
│  Tone Examples:                                        │
│  ┌─────────────────────────────────────────────────┐  │
│  │ "I noticed your usage dropped this week. Is     │  │
│  │  everything okay? I'm here to help!"            │  │
│  │                                                  │  │
│  │ "Let me walk you through how to get the most   │  │
│  │  value from this feature."                      │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  [← Back]  [Next: Capabilities →]                     │
└─────────────────────────────────────────────────────────┘
```

**Step 3: Capabilities & Permissions**

```
┌─────────────────────────────────────────────────────────┐
│  Create New VE - Step 3 of 6: Capabilities             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Can This VE Delegate Work to Others?                  │
│  (•) Yes, can delegate    ( ) No delegation            │
│                                                         │
│  Who can this VE delegate to?                          │
│  [✓] Senior-level VEs in same department               │
│  [✓] Junior-level VEs in same department               │
│  [ ] VEs in other departments                          │
│  [ ] Any VE in customer's organization                 │
│                                                         │
│  Decision-Making Authority:                            │
│  [✓] Can make autonomous decisions up to $X budget     │
│      Budget limit: [$1,000        ]                    │
│  [✓] Can approve work from subordinates                │
│  [✓] Can reassign tasks if quality is insufficient     │
│  [ ] Requires human approval for all actions           │
│                                                         │
│  Special Capabilities:                                 │
│  [✓] Memory/Context retention across conversations    │
│  [✓] Access to company knowledge base (RAG)            │
│  [✓] Can create and update internal documentation      │
│  [✓] Proactive outreach (can initiate conversations)   │
│  [ ] Schedule meetings/appointments                    │
│  [ ] Make purchases/transactions                       │
│                                                         │
│  [← Back]  [Next: Select Tools →]                     │
└─────────────────────────────────────────────────────────┘
```

**Step 4: Tools & Integrations**

```
┌─────────────────────────────────────────────────────────┐
│  Create New VE - Step 4 of 6: Tools & MCP Servers      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Available Tools:          [Search tools...          ] │
│                                                         │
│  ┌─ Built-in Tools ────────────────────────────────┐   │
│  │                                                  │   │
│  │ [✓] Company Knowledge Base (RAG Search)         │   │
│  │     Query company documents and knowledge       │   │
│  │                                                  │   │
│  │ [✓] Customer Database Query                     │   │
│  │     Read customer data, usage stats, etc.       │   │
│  │                                                  │   │
│  │ [✓] Send Email/Message                          │   │
│  │     Communicate with customers and other VEs    │   │
│  │                                                  │   │
│  │ [ ] Web Search                                  │   │
│  │     Search the internet for information         │   │
│  │                                                  │   │
│  │ [ ] Calendar Access                             │   │
│  │     Schedule and manage appointments            │   │
│  │                                                  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─ MCP Servers ──────────────────────────────────┐   │
│  │                                                  │   │
│  │ [✓] Supabase MCP Server                         │   │
│  │     Database operations via MCP protocol        │   │
│  │     [Configure]                                 │   │
│  │                                                  │   │
│  │ [ ] Slack MCP Server                            │   │
│  │     Send messages, read channels via Slack      │   │
│  │     [Configure]                                 │   │
│  │                                                  │   │
│  │ [ ] HubSpot MCP Server                          │   │
│  │     CRM operations                              │   │
│  │     [Configure]                                 │   │
│  │                                                  │   │
│  │ [+ Add Custom MCP Server]                       │   │
│  │                                                  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─ Custom Tools ─────────────────────────────────┐   │
│  │                                                  │   │
│  │ [+ Create Custom Tool]                          │   │
│  │ [+ Import Tool from Library]                    │   │
│  │                                                  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  [← Back]  [Next: Configure Pricing →]                │
└─────────────────────────────────────────────────────────┘
```

**Step 5: Pricing & Billing**

```
┌─────────────────────────────────────────────────────────┐
│  Create New VE - Step 5 of 6: Pricing                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Monthly Subscription Fee:                             │
│  $[99  ]/month                                         │
│                                                         │
│  Pricing Tier Recommendation:                          │
│  Based on seniority level (Manager), we recommend:     │
│  • Junior: $29-39/month                                │
│  • Senior: $59-79/month                                │
│  • Manager: $99-149/month ✓                            │
│                                                         │
│  Token Usage Billing:                                  │
│  (•) Customer pays for tokens used (recommended)       │
│  ( ) Included in monthly fee (risky for you!)          │
│                                                         │
│  Estimated Token Usage per Month:                      │
│  Based on similar VEs:                                 │
│  • Light use: ~50,000 tokens ($25)                     │
│  • Medium use: ~150,000 tokens ($75)                   │
│  • Heavy use: ~400,000 tokens ($200)                   │
│                                                         │
│  [Show Advanced Pricing Options]                       │
│                                                         │
│  [← Back]  [Next: Review & Deploy →]                  │
└─────────────────────────────────────────────────────────┘
```

**Step 6: Review & Deploy**

```
┌─────────────────────────────────────────────────────────┐
│  Create New VE - Step 6 of 6: Review & Deploy          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  VE Summary:                                           │
│  ─────────────────────────────────────────────────     │
│                                                         │
│  Name: Customer Success Manager                        │
│  Department: Customer Success                          │
│  Level: Manager                                        │
│  Persona: Rachel Thompson                              │
│                                                         │
│  Capabilities:                                         │
│  ✓ Can delegate to Senior/Junior                       │
│  ✓ Autonomous decisions up to $1,000                   │
│  ✓ Memory/Context retention                            │
│  ✓ Proactive outreach                                  │
│                                                         │
│  Tools:                                                │
│  • Company Knowledge Base (RAG)                        │
│  • Customer Database Query                             │
│  • Send Email/Message                                  │
│  • Supabase MCP Server                                 │
│                                                         │
│  Pricing: $99/month + token usage                      │
│                                                         │
│  Status:                                               │
│  (•) Beta     ( ) Alpha     ( ) Stable                │
│  (Only your team can test Beta VEs)                    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Preview Generated Configuration:                │  │
│  │                                                  │  │
│  │  [View YAML] [View JSON] [View CrewAI Code]    │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Deployment Options:                                   │
│  (•) Deploy to test environment first                  │
│  ( ) Deploy directly to marketplace (production)       │
│                                                         │
│  Test with sample scenarios?                           │
│  [✓] Yes, run automated tests before deploying         │
│                                                         │
│  [← Back]  [Save as Draft]  [Deploy VE →]            │
└─────────────────────────────────────────────────────────┘
```

---

## Interface 2: Hybrid Studio (Visual + YAML)

### Split-Screen Editor

```
┌─────────────────────────────────────────────────────────┐
│  VE Editor: Customer Success Manager                   │
│  [Visual] [Hybrid ✓] [Code]    [Save] [Test] [Deploy] │
├───────────────────────┬─────────────────────────────────┤
│  Visual Builder       │  Generated YAML (Live Preview)  │
│  (Left Panel)         │  (Right Panel)                  │
├───────────────────────┼─────────────────────────────────┤
│                       │                                 │
│  Name:                │  apiVersion: kagent.solo.io/v1  │
│  [Customer Success    │  kind: Agent                    │
│   Manager          ]  │  metadata:                      │
│                       │    name: customer-success-mgr   │
│  Department:          │    labels:                      │
│  [Customer Success ▼] │      department: customer-succ. │
│                       │      seniority: manager         │
│  Seniority:           │      status: beta               │
│  (•) Manager          │  spec:                          │
│                       │    framework: crewai            │
│  Delegation:          │    config:                      │
│  [✓] Can delegate     │      role: "Customer Success    │
│                       │             Manager"            │
│  Tools:               │      goal: "Ensure customer     │
│  [✓] RAG Search       │             satisfaction..."    │
│  [✓] DB Query         │      backstory: |               │
│  [✓] Send Message     │        You have 10 years...     │
│                       │      allow_delegation: true     │
│  [Edit Advanced...]   │      tools:                     │
│                       │        - query_knowledge_base   │
│                       │        - query_customer_db      │
│                       │        - send_message           │
│                       │      memory: true               │
│                       │      verbose: true              │
│                       │                                 │
│  [Sync Visual ↔ YAML] │  [Copy] [Download] [Validate]  │
└───────────────────────┴─────────────────────────────────┘
```

**Key Features:**
- **Live Sync**: Changes in visual update YAML immediately
- **Bi-directional**: Edit YAML directly, visual updates
- **Validation**: Real-time syntax checking
- **Templates**: Start from templates, customize in YAML

---

## Interface 3: Developer CLI (Full Code)

### YAML Configuration Files

**VE Definition YAML:**

```yaml
# ve-customer-success-manager.yaml
apiVersion: ve-platform.io/v1
kind: VirtualEmployee
metadata:
  name: customer-success-manager
  labels:
    department: customer-success
    seniority: manager
    status: beta
    version: "1.0.0"
  annotations:
    created-by: "admin@company.com"
    created-at: "2025-11-23"

spec:
  # Basic Information
  display_name: "Customer Success Manager"
  default_persona_name: "Rachel Thompson"
  description: "Manages customer success initiatives, ensures retention, and drives expansion revenue"
  
  # Personality & Behavior
  personality:
    role: "Customer Success Manager"
    goal: "Ensure customer satisfaction, retention, and expansion"
    backstory: |
      You have 10 years of experience in B2B SaaS customer success.
      You believe in proactive outreach and data-driven decision making.
      You always put the customer first and focus on long-term relationships.
    communication_style: "professional-empathetic"
    tone_examples:
      - "I noticed your usage dropped this week. Is everything okay? I'm here to help!"
      - "Let me walk you through how to get the most value from this feature."
  
  # Framework Configuration
  framework:
    type: crewai
    version: "0.1.0"
    config:
      allow_delegation: true
      memory: true
      verbose: false
      max_iter: 25
      max_rpm: 10
  
  # Capabilities & Permissions
  capabilities:
    delegation:
      enabled: true
      can_delegate_to:
        - senior_level
        - junior_level
      same_department_only: true
    
    decision_making:
      autonomous_up_to_amount: 1000
      requires_approval_above: 1000
      can_approve_subordinate_work: true
      can_reassign_tasks: true
    
    features:
      - memory_retention
      - rag_access
      - proactive_outreach
      - documentation_creation
  
  # Tools & MCP Servers
  tools:
    - name: query_knowledge_base
      type: builtin
      config:
        source: company_rag
        max_results: 10
    
    - name: query_customer_database
      type: builtin
      config:
        tables:
          - customers
          - usage_stats
          - support_tickets
        readonly: true
    
    - name: send_message
      type: builtin
      config:
        can_email: true
        can_chat: true
        can_message_ves: true
  
  mcp_servers:
    - name: supabase
      url: "${SUPABASE_MCP_URL}"
      auth:
        type: api_key
        secret_ref: supabase-mcp-key
      permissions:
        - read:customers
        - read:usage_stats
        - write:customer_notes
    
    - name: hubspot
      url: "${HUBSPOT_MCP_URL}"
      auth:
        type: oauth
        secret_ref: hubspot-oauth
      permissions:
        - read:contacts
        - write:notes
        - read:deals
  
  # LLM Configuration
  llm:
    default_model: "gpt-4-turbo"
    fallback_models:
      - "gpt-4"
      - "claude-3-sonnet"
    temperature: 0.7
    max_tokens: 4000
  
  # Pricing
  pricing:
    monthly_fee: 99.00
    currency: "USD"
    token_billing: "customer_pays"
    estimated_token_usage:
      light: 50000
      medium: 150000
      heavy: 400000
  
  # Deployment
  deployment:
    status: "beta"  # beta | alpha | stable
    min_replicas: 1
    max_replicas: 10
    auto_scaling: true
    resources:
      cpu: "500m"
      memory: "1Gi"
  
  # Testing & Quality
  quality:
    required_tests:
      - test_delegation
      - test_customer_interaction
      - test_data_analysis
    min_success_rate: 0.85
    review_required: true
```

**MCP Server Definition:**

```yaml
# mcp-customer-health-monitor.yaml
apiVersion: mcp.ve-platform.io/v1
kind: MCPServer
metadata:
  name: customer-health-monitor
  labels:
    category: analytics
    department: customer-success

spec:
  description: "Monitor customer health metrics and provide insights"
  
  # Server Configuration
  server:
    type: custom
    image: "your-registry/customer-health-mcp:1.0.0"
    port: 8080
    protocol: http
    
  # Authentication
  auth:
    required: true
    methods:
      - api_key
      - oauth2
  
  # Tools Exposed
  tools:
    - name: get_customer_health_score
      description: "Calculate customer health score based on usage, support tickets, and engagement"
      input_schema:
        type: object
        properties:
          customer_id:
            type: string
            description: "Customer UUID"
          time_range:
            type: string
            enum: ["7d", "30d", "90d"]
        required: ["customer_id"]
      
      output_schema:
        type: object
        properties:
          health_score:
            type: number
            minimum: 0
            maximum: 100
          factors:
            type: object
          recommendations:
            type: array
    
    - name: predict_churn_risk
      description: "Predict likelihood of customer churning"
      input_schema:
        type: object
        properties:
          customer_id:
            type: string
        required: ["customer_id"]
      
      output_schema:
        type: object
        properties:
          churn_probability:
            type: number
          risk_level:
            type: string
            enum: ["low", "medium", "high"]
          contributing_factors:
            type: array
  
  # Resources Exposed
  resources:
    - name: customer_engagement_data
      description: "Historical customer engagement metrics"
      uri_template: "customers/{customer_id}/engagement"
      mime_type: "application/json"
  
  # Deployment
  deployment:
    replicas: 2
    resources:
      cpu: "250m"
      memory: "512Mi"
    health_check:
      path: "/health"
      interval: 30s
```

**Custom Tool Definition:**

```yaml
# tool-sentiment-analyzer.yaml
apiVersion: tools.ve-platform.io/v1
kind: CustomTool
metadata:
  name: sentiment-analyzer
  labels:
    category: nlp
    use_case: customer-support

spec:
  name: analyze_sentiment
  description: "Analyze sentiment of customer messages"
  
  # Tool Type
  type: function
  
  # Function Definition
  function:
    language: python
    runtime: python3.11
    handler: "sentiment.analyze"
    
    # Code (inline or reference)
    code: |
      import openai
      
      def analyze(message: str) -> dict:
          """Analyze sentiment of message"""
          response = openai.chat.completions.create(
              model="gpt-4",
              messages=[{
                  "role": "system",
                  "content": "Analyze sentiment. Return: positive, negative, or neutral with confidence score."
              }, {
                  "role": "user",
                  "content": message
              }]
          )
          return parse_sentiment(response)
    
    # Or reference external code
    code_ref:
      type: git
      repo: "https://github.com/yourorg/ve-tools"
      path: "tools/sentiment.py"
      branch: "main"
  
  # Input/Output Schema
  input_schema:
    type: object
    properties:
      message:
        type: string
        description: "Message to analyze"
    required: ["message"]
  
  output_schema:
    type: object
    properties:
      sentiment:
        type: string
        enum: ["positive", "negative", "neutral"]
      confidence:
        type: number
        minimum: 0
        maximum: 1
      explanation:
        type: string
  
  # Dependencies
  dependencies:
    packages:
      - openai==1.3.0
      - numpy==1.24.0
    
    env_vars:
      - name: OPENAI_API_KEY
        secret_ref: openai-api-key
  
  # Testing
  test_cases:
    - name: positive_sentiment
      input:
        message: "This product is amazing! Love it!"
      expected_output:
        sentiment: "positive"
        confidence: ">0.8"
    
    - name: negative_sentiment
      input:
        message: "Worst experience ever. Terrible!"
      expected_output:
        sentiment: "negative"
        confidence: ">0.8"
```

---

## CLI Commands

### VE Management

```bash
# Install CLI
npm install -g @ve-platform/cli
# or
pip install ve-platform-cli

# Login
ve-cli login

# Create VE from YAML
ve-cli ve create -f ve-customer-success-manager.yaml

# List VEs
ve-cli ve list

# Get VE details
ve-cli ve get customer-success-manager

# Update VE
ve-cli ve apply -f ve-customer-success-manager-v2.yaml

# Delete VE
ve-cli ve delete customer-success-manager

# Test VE before deploying
ve-cli ve test -f ve-customer-success-manager.yaml \
  --scenario test-scenarios/cs-manager-tests.yaml

# Deploy to marketplace
ve-cli ve deploy customer-success-manager \
  --status beta \
  --marketplace true

# Promote VE status
ve-cli ve promote customer-success-manager \
  --from beta --to alpha

# Export VE config
ve-cli ve export customer-success-manager \
  --format yaml \
  --output ve-export.yaml
```

### MCP Server Management

```bash
# Create MCP server
ve-cli mcp create -f mcp-customer-health-monitor.yaml

# List MCP servers
ve-cli mcp list

# Test MCP server
ve-cli mcp test customer-health-monitor \
  --tool get_customer_health_score \
  --input '{"customer_id": "test-123"}'

# Deploy MCP server
ve-cli mcp deploy customer-health-monitor

# View logs
ve-cli mcp logs customer-health-monitor --follow
```

### Tool Management

```bash
# Create custom tool
ve-cli tool create -f tool-sentiment-analyzer.yaml

# List tools
ve-cli tool list

# Test tool
ve-cli tool test sentiment-analyzer \
  --input '{"message": "This is great!"}'

# Publish to tool library
ve-cli tool publish sentiment-analyzer \
  --visibility public
```

---

## Git-Based Workflow (Recommended for Production)

### Repository Structure

```
ve-platform-config/
├── ves/
│   ├── marketing/
│   │   ├── marketing-manager.yaml
│   │   ├── marketing-senior.yaml
│   │   └── marketing-junior.yaml
│   ├── support/
│   │   ├── support-manager.yaml
│   │   └── support-junior.yaml
│   └── sales/
│       └── sales-manager.yaml
├── mcp-servers/
│   ├── supabase-mcp.yaml
│   ├── customer-health-monitor.yaml
│   └── hubspot-mcp.yaml
├── tools/
│   ├── sentiment-analyzer.yaml
│   ├── email-generator.yaml
│   └── data-analyzer.yaml
├── tests/
│   ├── ve-tests/
│   └── mcp-tests/
└── .github/
    └── workflows/
        ├── deploy-ves.yaml
        └── test-ves.yaml
```

### CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy-ves.yaml
name: Deploy VEs to Platform

on:
  push:
    branches: [main]
    paths:
      - 'ves/**'

jobs:
  validate-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install VE CLI
        run: npm install -g @ve-platform/cli
      
      - name: Login to Platform
        run: ve-cli login --token ${{ secrets.VE_PLATFORM_TOKEN }}
      
      - name: Validate VE Configs
        run: |
          for file in ves/**/*.yaml; do
            ve-cli ve validate -f $file
          done
      
      - name: Run Tests
        run: |
          for file in ves/**/*.yaml; do
            ve-cli ve test -f $file --scenarios tests/ve-tests/
          done
      
      - name: Deploy to Staging
        run: |
          for file in ves/**/*.yaml; do
            ve-cli ve deploy -f $file --env staging
          done
      
      - name: Run Integration Tests
        run: ve-cli test integration --env staging
      
      - name: Deploy to Production
        if: success()
        run: |
          for file in ves/**/*.yaml; do
            ve-cli ve deploy -f $file --env production
          done
```

---

## Admin Dashboard Overview

### VE Management Dashboard

```
┌─────────────────────────────────────────────────────────┐
│  VE Platform Admin                   [admin@company.com]│
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [VEs] [MCP Servers] [Tools] [Analytics] [Settings]    │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  Virtual Employees (23 total)      [+ Create New VE]    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Filters: [All ▼] [Status: All ▼] [Dept: All ▼]       │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Customer Success Manager          [Beta Badge]   │  │
│  │ Department: Customer Success      Manager        │  │
│  │ Active instances: 12                             │  │
│  │ Avg rating: 4.8/5.0                              │  │
│  │ Revenue: $1,188/month                            │  │
│  │ [Edit] [Test] [Promote to Alpha] [Analytics]    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Marketing Manager                 [Stable Badge] │  │
│  │ Department: Marketing             Manager        │  │
│  │ Active instances: 47                             │  │
│  │ Avg rating: 4.9/5.0                              │  │
│  │ Revenue: $4,653/month                            │  │
│  │ [Edit] [Test] [Clone] [Analytics] [Deprecate]   │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Support Junior                    [Alpha Badge]  │  │
│  │ Department: Support               Junior         │  │
│  │ Active instances: 89                             │  │
│  │ Avg rating: 4.6/5.0                              │  │
│  │ Revenue: $2,581/month                            │  │
│  │ [Edit] [Test] [Promote to Stable] [Analytics]   │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  [Load More VEs...]                                    │
└─────────────────────────────────────────────────────────┘
```

---

## Testing Interface

### VE Testing Dashboard

```
┌─────────────────────────────────────────────────────────┐
│  Test VE: Customer Success Manager                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Test Scenarios:              [+ Create New Scenario]   │
│                                                         │
│  ┌─ Built-in Scenarios ──────────────────────────────┐ │
│  │                                                    │ │
│  │ [✓] Basic Task Delegation                         │ │
│  │     Test if VE can delegate to subordinates       │ │
│  │     Status: ✅ Passed (12/12 tests)               │ │
│  │     [Run Again] [View Results]                    │ │
│  │                                                    │ │
│  │ [✓] Customer Interaction Quality                  │ │
│  │     Test communication style and empathy          │ │
│  │     Status: ✅ Passed (8/8 tests)                 │ │
│  │     [Run Again] [View Results]                    │ │
│  │                                                    │ │
│  │ [✓] Data Analysis & Insights                      │ │
│  │     Test ability to analyze customer data         │ │
│  │     Status: ⚠️ Partial (5/7 tests passed)        │ │
│  │     [Run Again] [View Failures] [Fix Issues]     │ │
│  │                                                    │ │
│  │ [✓] Error Handling                                │ │
│  │     Test response to errors and edge cases        │ │
│  │     Status: ✅ Passed (10/10 tests)               │ │
│  │     [Run Again] [View Results]                    │ │
│  │                                                    │ │
│  │ [ ] Stress Test (1000 concurrent requests)       │ │
│  │     Test performance under load                   │ │
│  │     Status: Not run                               │ │
│  │     [Run Test]                                    │ │
│  │                                                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                         │
│  ┌─ Custom Scenarios ─────────────────────────────────┐ │
│  │                                                    │ │
│  │ [✓] Churn Prevention Workflow                     │ │
│  │     Custom scenario: Detect and prevent churn     │ │
│  │     Status: ✅ Passed (15/15 tests)               │ │
│  │     [Edit] [Run] [View Results]                   │ │
│  │                                                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                         │
│  Overall Test Score: 92% (50/54 tests passed)          │
│                                                         │
│  [Run All Tests] [Generate Test Report] [Export]       │
└─────────────────────────────────────────────────────────┘
```

### Creating a Test Scenario

```
┌─────────────────────────────────────────────────────────┐
│  Create Test Scenario                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Scenario Name:                                        │
│  [Escalation Handling Test                          ]  │
│                                                         │
│  Description:                                          │
│  ┌─────────────────────────────────────────────────┐  │
│  │Test how VE handles angry customer escalations   │  │
│  │and whether it properly routes to manager        │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Test Steps:                                           │
│  ┌─────────────────────────────────────────────────┐  │
│  │ 1. Input: Angry customer message                │  │
│  │    Expected: VE detects high sentiment negativity│  │
│  │                                                  │  │
│  │ 2. Input: Customer demands refund                │  │
│  │    Expected: VE escalates to manager             │  │
│  │                                                  │  │
│  │ 3. Input: Follow-up after escalation             │  │
│  │    Expected: Empathetic response with solution   │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Test Data:                                            │
│  ┌─────────────────────────────────────────────────┐  │
│  │ customer_message: "This is ridiculous! I've been│  │
│  │                   waiting 3 hours and nothing    │  │
│  │                   works. I want my money back!"  │  │
│  │                                                  │  │
│  │ customer_sentiment: "highly_negative"           │  │
│  │ customer_tier: "premium"                        │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Success Criteria:                                     │
│  [✓] Response time < 10 seconds                        │
│  [✓] Sentiment analysis accuracy > 90%                 │
│  [✓] Escalation triggered correctly                    │
│  [✓] Response includes empathy and solution            │
│                                                         │
│  [Cancel] [Save] [Save & Run Test]                     │
└─────────────────────────────────────────────────────────┘
```

---

## Analytics & Monitoring

### VE Performance Dashboard

```
┌─────────────────────────────────────────────────────────┐
│  Analytics: Customer Success Manager VE                 │
│  Last 30 Days                          [Export Report]  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─ Key Metrics ─────────────────────────────────────┐ │
│  │                                                    │ │
│  │  Active Instances:    12                          │ │
│  │  Total Tasks:         847                         │ │
│  │  Avg Response Time:   4.2 min                     │ │
│  │  Success Rate:        94.3%                       │ │
│  │  Customer Rating:     4.8/5.0                     │ │
│  │  Token Usage:         1.2M tokens                 │ │
│  │  Avg Cost/Task:       $0.42                       │ │
│  │                                                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                         │
│  ┌─ Usage Trend ──────────────────────────────────────┐ │
│  │                                                    │ │
│  │  Tasks Completed Over Time:                       │ │
│  │                                                    │ │
│  │   60 │                       ╱╲                   │ │
│  │   50 │           ╱╲         ╱  ╲                  │ │
│  │   40 │      ╱╲  ╱  ╲       ╱    ╲                 │ │
│  │   30 │     ╱  ╲╱    ╲  ╱╲ ╱      ╲                │ │
│  │   20 │    ╱           ╲╱  ╲        ╲___           │ │
│  │   10 │___╱                   ╲                    │ │
│  │      └────────────────────────────────────────    │ │
│  │       Week 1  Week 2  Week 3  Week 4             │ │
│  │                                                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                         │
│  ┌─ Top Issues ───────────────────────────────────────┐ │
│  │                                                    │ │
│  │  1. Customer health score calculation (23 times)  │ │
│  │  2. Usage drop alerts (18 times)                  │ │
│  │  3. Expansion opportunity identification (15x)    │ │
│  │  4. Onboarding assistance (12 times)              │ │
│  │  5. Feature adoption tracking (9 times)           │ │
│  │                                                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                         │
│  ┌─ Customer Feedback ────────────────────────────────┐ │
│  │                                                    │ │
│  │  ⭐⭐⭐⭐⭐ "Rachel is amazing! Proactive and helpful"│ │
│  │  ⭐⭐⭐⭐⭐ "Best CS manager I've worked with"       │ │
│  │  ⭐⭐⭐⭐☆ "Great, but sometimes too many follow-ups"│ │
│  │  ⭐⭐⭐⭐⭐ "Saved us from churning twice"           │ │
│  │                                                    │ │
│  │  [View All Feedback (47)]                         │ │
│  │                                                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                         │
│  [View Detailed Analytics] [Compare with Other VEs]     │
└─────────────────────────────────────────────────────────┘
```

---

## My Recommendation for You

### Start with: **Hybrid Studio (Visual + YAML)**

**Why:**
1. ✅ **Visual builder** for speed and ease
2. ✅ **YAML preview** so you learn the structure
3. ✅ **Easy export** to move to CLI later
4. ✅ **Live validation** catches errors immediately
5. ✅ **Best of both worlds**

### Your Workflow:

**Step 1: Use Visual Builder for First VE**
```
Create your first VE (e.g., Customer Success Manager) using the 
visual wizard. See the YAML being generated in real-time.
```

**Step 2: Export and Understand YAML**
```
Export the YAML, study it, understand the structure. This becomes
your template for future VEs.
```

**Step 3: Clone and Modify**
```
For similar VEs (e.g., Sales Manager), clone the YAML and modify.
Use hybrid studio to make changes visually or in YAML.
```

**Step 4: Graduate to CLI**
```
Once comfortable, move to Git-based workflow with CLI for
version control and CI/CD automation.
```

---

## Quick Start Guide for Admins

### Creating Your First VE in 10 Minutes

**1. Login to Admin Dashboard**
```
https://admin.ve-platform.com
Login with your admin credentials
```

**2. Click "Create New VE"**
```
Choose: "Visual Builder" (recommended for first time)
```

**3. Fill Out 6 Steps**
```
Step 1: Basic Info (name, department, level)
Step 2: Personality (role, backstory, communication style)
Step 3: Capabilities (delegation, decision-making)
Step 4: Tools (select from available tools/MCP servers)
Step 5: Pricing (set monthly fee)
Step 6: Review and Deploy
```

**4. Deploy to Test Environment**
```
Click "Deploy to Test"
Wait 2-3 minutes for deployment
```

**5. Test Your VE**
```
Go to "Test VE" page
Run built-in test scenarios
Create custom test with sample customer interaction
```

**6. Deploy to Marketplace**
```
If tests pass:
- Set status to "Beta"
- Deploy to marketplace
- Only you can see Beta VEs initially
```

**7. Iterate Based on Usage**
```
Monitor analytics
Gather feedback from test customers
Refine and improve
Promote to Alpha → Stable when ready
```

---

## Advanced: Template Library

### Pre-built VE Templates

```
┌─────────────────────────────────────────────────────────┐
│  VE Templates                        [+ Upload Template]│
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Official Templates (Maintained by Platform Team):     │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 📧 Email Marketing Specialist                    │  │
│  │    Senior level, includes email tools            │  │
│  │    [Use Template] [Preview]                      │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 📞 Customer Support Agent                        │  │
│  │    Junior level, ticket management focused       │  │
│  │    [Use Template] [Preview]                      │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 📊 Data Analyst                                  │  │
│  │    Senior level, analytics and reporting         │  │
│  │    [Use Template] [Preview]                      │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Community Templates:                                  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 🎨 Social Media Manager                          │  │
│  │    By: @acme-corp | ⭐ 4.7/5.0 | 23 uses        │  │
│  │    [Use Template] [Preview] [Fork]               │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Your Templates:                                       │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Custom CS Manager Template                       │  │
│  │    Created: 2025-11-01 | Private                 │  │
│  │    [Edit] [Use] [Share] [Delete]                 │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## MCP Server Creation Interface

### Visual MCP Builder

```
┌─────────────────────────────────────────────────────────┐
│  Create MCP Server                                      │
│  Step 1 of 4: Basic Configuration                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Server Name:                                          │
│  [customer-lifecycle-analytics                      ]  │
│                                                         │
│  Description:                                          │
│  ┌─────────────────────────────────────────────────┐  │
│  │Provides customer lifecycle analytics including   │  │
│  │onboarding progress, engagement metrics, and      │  │
│  │churn prediction                                  │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Category:                                             │
│  [Analytics ▼]                                         │
│   • Data & Analytics ✓                                │
│   • Communication                                      │
│   • CRM & Sales                                        │
│   • Project Management                                 │
│   • Custom                                             │
│                                                         │
│  Server Type:                                          │
│  (•) Docker Container (recommended)                    │
│  ( ) Serverless Function                               │
│  ( ) External API Wrapper                              │
│                                                         │
│  [Next: Define Tools →]                                │
└─────────────────────────────────────────────────────────┘
```

**Step 2: Define Tools**

```
┌─────────────────────────────────────────────────────────┐
│  Create MCP Server - Step 2 of 4: Tools                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Tools Exposed by This Server:    [+ Add Tool]         │
│                                                         │
│  ┌─ Tool 1 ──────────────────────────────────────────┐ │
│  │                                                    │ │
│  │  Tool Name: get_lifecycle_stage                   │ │
│  │  Description: Get current lifecycle stage of      │ │
│  │               customer                            │ │
│  │                                                    │ │
│  │  Input Parameters:                                │ │
│  │  ┌────────────────────────────────────────────┐  │ │
│  │  │ customer_id (string, required)             │  │ │
│  │  │   Description: Customer UUID                │  │ │
│  │  └────────────────────────────────────────────┘  │ │
│  │                                                    │ │
│  │  Output Format:                                   │ │
│  │  ┌────────────────────────────────────────────┐  │ │
│  │  │ {                                          │  │ │
│  │  │   "stage": "onboarding|active|at_risk|...",│  │ │
│  │  │   "days_in_stage": number,                 │  │ │
│  │  │   "next_milestone": string                 │  │ │
│  │  │ }                                          │  │ │
│  │  └────────────────────────────────────────────┘  │ │
│  │                                                    │ │
│  │  [Edit] [Test] [Remove]                          │ │
│  │                                                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                         │
│  ┌─ Tool 2 ──────────────────────────────────────────┐ │
│  │                                                    │ │
│  │  Tool Name: predict_churn                        │ │
│  │  Description: Predict churn probability           │ │
│  │  [Edit] [Test] [Remove]                          │ │
│  │                                                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                         │
│  [← Back] [Next: Configure Resources →]               │
└─────────────────────────────────────────────────────────┘
```

**Step 3: Code/Container Configuration**

```
┌─────────────────────────────────────────────────────────┐
│  Create MCP Server - Step 3 of 4: Implementation       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Implementation Method:                                │
│  (•) Use Docker Image                                  │
│  ( ) Write Code Inline                                 │
│  ( ) Reference Git Repository                          │
│                                                         │
│  Docker Image:                                         │
│  [your-registry/lifecycle-analytics:1.0.0           ]  │
│                                                         │
│  Port: [8080  ]                                        │
│                                                         │
│  Environment Variables:                                │
│  ┌─────────────────────────────────────────────────┐  │
│  │ DATABASE_URL = ${SUPABASE_URL}                  │  │
│  │ API_KEY = secret:analytics-api-key              │  │
│  └─────────────────────────────────────────────────┘  │
│  [+ Add Variable]                                      │
│                                                         │
│  Health Check:                                         │
│  Path: [/health            ]                           │
│  Interval: [30] seconds                                │
│                                                         │
│  Resources:                                            │
│  CPU: [250m ▼]    Memory: [512Mi ▼]                   │
│  Replicas: Min [1] Max [10]                            │
│                                                         │
│  [← Back] [Next: Test & Deploy →]                     │
└─────────────────────────────────────────────────────────┘
```

---

## Custom Tool Creation

### Inline Code Tool Builder

```
┌─────────────────────────────────────────────────────────┐
│  Create Custom Tool                                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Tool Name: [email_template_generator               ]  │
│                                                         │
│  Description:                                          │
│  [Generate professional email templates based on       ]│
│  [context and recipient type                          ]│
│                                                         │
│  Language: [Python ▼]                                  │
│                                                         │
│  Code Editor:                                          │
│  ┌─────────────────────────────────────────────────┐  │
│  │ from typing import Dict                         │  │
│  │ import openai                                   │  │
│  │                                                  │  │
│  │ def generate_email_template(                    │  │
│  │     recipient_type: str,                        │  │
│  │     purpose: str,                               │  │
│  │     tone: str = "professional"                  │  │
│  │ ) -> Dict[str, str]:                            │  │
│  │     """                                         │  │
│  │     Generate email template                     │  │
│  │                                                  │  │
│  │     Args:                                       │  │
│  │         recipient_type: customer, prospect, etc.│  │
│  │         purpose: welcome, followup, etc.        │  │
│  │         tone: professional, casual, formal      │  │
│  │                                                  │  │
│  │     Returns:                                    │  │
│  │         Dict with subject and body              │  │
│  │     """                                         │  │
│  │     prompt = f"""                               │  │
│  │     Generate an email template for {purpose}    │  │
│  │     Recipient: {recipient_type}                 │  │
│  │     Tone: {tone}                                │  │
│  │     """                                         │  │
│  │                                                  │  │
│  │     response = openai.chat.completions.create( │  │
│  │         model="gpt-4",                          │  │
│  │         messages=[{"role": "system",            │  │
│  │                   "content": prompt}]           │  │
│  │     )                                           │  │
│  │                                                  │  │
│  │     return {                                    │  │
│  │         "subject": extract_subject(response),   │  │
│  │         "body": extract_body(response)          │  │
│  │     }                                           │  │
│  │                                                  │  │
│  └─────────────────────────────────────────────────┘  │
│  [Format Code] [Validate Syntax] [Test Function]       │
│                                                         │
│  Dependencies:                                         │
│  [openai==1.3.0                                     ]  │
│  [+ Add Package]                                       │
│                                                         │
│  Test Input:                                           │
│  ┌─────────────────────────────────────────────────┐  │
│  │ {                                               │  │
│  │   "recipient_type": "customer",                 │  │
│  │   "purpose": "welcome",                         │  │
│  │   "tone": "professional"                        │  │
│  │ }                                               │  │
│  └─────────────────────────────────────────────────┘  │
│  [Run Test]                                            │
│                                                         │
│  [Cancel] [Save] [Deploy Tool]                         │
└─────────────────────────────────────────────────────────┘
```

---

## Version Control & Rollback

### VE Version History

```
┌─────────────────────────────────────────────────────────┐
│  Customer Success Manager - Version History             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─ Current Version (v3.2.1) ────────────────────────┐ │
│  │  Status: Stable                                   │ │
│  │  Deployed: 2025-11-20                             │ │
│  │  Active Instances: 12                             │ │
│  │  Performance: 94.3% success rate                  │ │
│  │  [Edit] [Clone] [Rollback to Previous]          │ │
│  └────────────────────────────────────────────────────┘ │
│                                                         │
│  Version History:                                      │
│                                                         │
│  ┌────────────────────────────────────────────────────┐│
│  │ v3.2.1 (Current) - 2025-11-20                     ││
│  │ • Fixed: Improved churn prediction accuracy       ││
│  │ • Added: Proactive outreach timing optimization   ││
│  │ 12 instances | 4.8★ | [View Changes] [Restore]   ││
│  └────────────────────────────────────────────────────┘│
│                                                         │
│  ┌────────────────────────────────────────────────────┐│
│  │ v3.2.0 - 2025-11-10                               ││
│  │ • Added: Integration with HubSpot MCP             ││
│  │ • Fixed: Response time improvements               ││
│  │ Deprecated | [View Changes] [Restore]             ││
│  └────────────────────────────────────────────────────┘│
│                                                         │
│  ┌────────────────────────────────────────────────────┐│
│  │ v3.1.0 - 2025-10-25                               ││
│  │ • Major: Added customer health scoring            ││
│  │ • Fixed: Delegation logic improvements            ││
│  │ Deprecated | [View Changes] [Restore]             ││
│  └────────────────────────────────────────────────────┘│
│                                                         │
│  [Load More Versions...]                               │
│                                                         │
│  [Compare Versions] [Create New Version]               │
└─────────────────────────────────────────────────────────┘
```

---

## Summary: Your Best Path Forward

### Recommended Approach

**Phase 1: Start Visual (Week 1)**
1. Use Visual Builder to create first VE
2. Understand the concepts through UI
3. See YAML generation in real-time
4. Deploy and test

**Phase 2: Hybrid Mode (Weeks 2-4)**
1. Switch to Hybrid Studio
2. Make visual changes, see YAML
3. Start making small YAML edits
4. Export configs to files

**Phase 3: CLI & Git (Month 2+)**
1. Move to YAML files in Git
2. Use CLI for deployments
3. Set up CI/CD pipeline
4. Full version control

### Why This Progressive Approach Works:

✅ **Start Fast**: Visual builder gets you productive immediately
✅ **Learn Gradually**: See YAML as you work visually
✅ **No Lock-in**: Can always export and move to code
✅ **Team Friendly**: Non-technical can use visual, technical can use CLI
✅ **Production Ready**: Git + CI/CD for serious deployments

### Tools You'll Use:

1. **Admin Dashboard** (web UI) - Day-to-day VE management
2. **Visual/Hybrid Studio** (web UI) - Creating/editing VEs
3. **CLI** (command line) - Automation and deployments
4. **Git** (version control) - Production workflow
5. **Test Runner** (web UI or CLI) - Quality assurance

---

**You now have complete flexibility to create VEs, MCP servers, and tools using whichever interface suits your needs - from fully visual to pure YAML/code!**