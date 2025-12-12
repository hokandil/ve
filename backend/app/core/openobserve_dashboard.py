"""
OpenObserve Dashboard Configuration for Delegation Tree Visualization
"""

DELEGATION_TREE_DASHBOARD = {
    "title": "Intelligent Delegation Tree",
    "description": "Visualize agent delegation decisions and execution flow",
    "panels": [
        {
            "title": "Delegation Decision Flow",
            "type": "trace",
            "query": """
                SELECT 
                    trace_id,
                    span_id,
                    parent_span_id,
                    span_name,
                    attributes.agent_type,
                    attributes.decision,
                    attributes.delegation_depth,
                    attributes.confidence,
                    start_time,
                    duration
                FROM temporal_traces
                WHERE span_name LIKE '%delegation%'
                ORDER BY start_time DESC
                LIMIT 100
            """,
            "visualization": "tree"
        },
        {
            "title": "Agent Decision Distribution",
            "type": "pie",
            "query": """
                SELECT 
                    attributes.decision as decision_type,
                    COUNT(*) as count
                FROM temporal_traces
                WHERE span_name = 'agent_decision'
                GROUP BY attributes.decision
            """
        },
        {
            "title": "Delegation Depth Histogram",
            "type": "histogram",
            "query": """
                SELECT 
                    attributes.delegation_depth as depth,
                    COUNT(*) as count
                FROM temporal_traces
                WHERE span_name LIKE '%delegation%'
                GROUP BY attributes.delegation_depth
                ORDER BY depth
            """
        },
        {
            "title": "Agent Confidence Scores",
            "type": "timeseries",
            "query": """
                SELECT 
                    time_bucket('1m', start_time) as time,
                    AVG(CAST(attributes.confidence AS FLOAT)) as avg_confidence,
                    attributes.agent_type
                FROM temporal_traces
                WHERE span_name = 'agent_decision'
                GROUP BY time, attributes.agent_type
                ORDER BY time DESC
            """
        },
        {
            "title": "Parallel Execution Count",
            "type": "stat",
            "query": """
                SELECT COUNT(*) as parallel_tasks
                FROM temporal_traces
                WHERE attributes.decision = 'parallel'
                AND start_time > NOW() - INTERVAL '1 hour'
            """
        },
        {
            "title": "Delegation Chain Length",
            "type": "bar",
            "query": """
                SELECT 
                    trace_id,
                    MAX(CAST(attributes.delegation_depth AS INT)) as max_depth
                FROM temporal_traces
                WHERE span_name LIKE '%delegation%'
                GROUP BY trace_id
                ORDER BY max_depth DESC
                LIMIT 20
            """
        }
    ]
}


DELEGATION_TRACE_QUERY = """
-- Query to visualize full delegation tree for a specific task
WITH RECURSIVE delegation_tree AS (
    -- Root: Initial delegation
    SELECT 
        trace_id,
        span_id,
        parent_span_id,
        span_name,
        attributes.agent_type as agent,
        attributes.decision,
        attributes.delegation_depth as depth,
        attributes.task_id,
        start_time,
        duration,
        0 as level
    FROM temporal_traces
    WHERE parent_span_id IS NULL
    AND attributes.task_id = :task_id
    
    UNION ALL
    
    -- Children: Recursive delegations
    SELECT 
        t.trace_id,
        t.span_id,
        t.parent_span_id,
        t.span_name,
        t.attributes.agent_type,
        t.attributes.decision,
        t.attributes.delegation_depth,
        t.attributes.task_id,
        t.start_time,
        t.duration,
        dt.level + 1
    FROM temporal_traces t
    INNER JOIN delegation_tree dt ON t.parent_span_id = dt.span_id
)
SELECT 
    trace_id,
    span_id,
    parent_span_id,
    agent,
    decision,
    depth,
    level,
    start_time,
    duration,
    REPEAT('  ', level) || agent || ' (' || decision || ')' as tree_view
FROM delegation_tree
ORDER BY start_time;
"""


# Environment variables for OpenObserve configuration
OPENOBSERVE_CONFIG = """
# Add to .env or k8s/configmaps.yaml

# OpenObserve OTLP Endpoint
OPENOBSERVE_OTLP_ENDPOINT=http://openobserve:5080

# OpenObserve Authentication
OPENOBSERVE_AUTH_TOKEN=<base64_encoded_user:password>

# OpenObserve Organization
OPENOBSERVE_ORG=default

# Enable tracing
ENABLE_TRACING=true
"""
