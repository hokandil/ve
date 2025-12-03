-- Security Audit Log Table
-- Logs all agent requests for security monitoring and compliance

CREATE TABLE IF NOT EXISTS security_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    customer_id UUID NOT NULL,
    path TEXT NOT NULL,
    method TEXT NOT NULL,
    context_hash TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    response_status INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX idx_security_audit_customer ON security_audit_log(customer_id, timestamp DESC);
CREATE INDEX idx_security_audit_timestamp ON security_audit_log(timestamp DESC);
CREATE INDEX idx_security_audit_hash ON security_audit_log(context_hash);

-- Add comment
COMMENT ON TABLE security_audit_log IS 'Audit log for all agent requests - used for security monitoring and compliance';
