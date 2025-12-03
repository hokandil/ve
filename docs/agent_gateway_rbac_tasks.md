# Agent Gateway RBAC - Remaining Tasks

## Completed ✅
- [x] Implement `gateway_config_service.py` with RBAC methods
- [x] Create default-deny TrafficPolicy on route creation
- [x] Update hire flow to grant access
- [x] Update unhire flow to revoke access (revert to deny-all)
- [x] Add delete agent endpoint
- [x] Test hire/unhire lifecycle
- [x] Verify secure by default behavior
- [x] Document implementation

## High Priority 🔴

### 1. Multi-Customer Testing
**Goal**: Verify multiple customers can hire the same agent and access is correctly managed.

**Steps**:
1. Create a second customer account (or use existing test account)
2. Customer A hires `wellness` agent
3. Customer B hires `wellness` agent
4. Verify TrafficPolicy contains both customer IDs
5. Customer A chats → should work
6. Customer B chats → should work
7. Customer A unhires
8. Verify TrafficPolicy only contains Customer B
9. Customer A chats → should fail (403)
10. Customer B chats → should still work

**Acceptance Criteria**:
- TrafficPolicy correctly maintains list of all hired customers
- Each customer can only access when they have hired
- Unhiring one customer doesn't affect others

### 2. Delete Agent Validation
**Goal**: Ensure agents cannot be deleted while customers are using them.

**Steps**:
1. Customer hires `wellness` agent
2. Admin attempts to delete `wellness` from marketplace
3. Verify API returns 400 error with message about active customers
4. Customer unhires agent
5. Admin deletes agent
6. Verify HTTPRoute and TrafficPolicy are deleted
7. Verify database record is deleted

**Acceptance Criteria**:
- Cannot delete agent with active customers
- Can delete agent with no customers
- All resources cleaned up on successful delete

### 3. Frontend Integration - Delete Agent
**Goal**: Add delete button to Admin UI for managing agents.

**Files to Modify**:
- `admin-frontend/src/pages/Marketplace.tsx` (or equivalent)

**Implementation**:
1. Add "Delete" button to each agent card/row
2. Show confirmation dialog before delete
3. Call `DELETE /api/discovery/agents/{ve_id}`
4. Handle 400 error (customers still using)
5. Show success/error toast
6. Refresh agent list

**Acceptance Criteria**:
- Admin can delete agents from UI
- Clear error message if customers are using agent
- UI updates after successful delete

## Medium Priority 🟡

### 4. Access Denied Testing
**Goal**: Verify that requests without proper authorization are blocked.

**Steps**:
1. Create curl script to test direct gateway access
2. Test without `X-Customer-ID` header → expect 403
3. Test with wrong `X-Customer-ID` → expect 403
4. Test with correct `X-Customer-ID` → expect 200
5. Test after unhire → expect 403

**Script Template**:
```bash
# Without header
curl -X POST http://localhost:8080/ \
  -H "Host: wellness.local" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"message/stream","params":{"message":{"kind":"message","messageId":"test","role":"user","parts":[{"kind":"text","text":"hello"}],"contextId":"test"}},"id":"1"}'

# With valid customer ID
curl -X POST http://localhost:8080/ \
  -H "Host: wellness.local" \
  -H "X-Customer-ID: ea15052d-1c39-4865-8ac0-f1160d44829f" \
  -H "Content-Type: application/json" \
  -d '...'
```

**Acceptance Criteria**:
- Requests without header are blocked
- Requests with wrong ID are blocked
- Requests with correct ID succeed

### 5. Automated Tests
**Goal**: Add pytest tests for RBAC flows.

**Test Cases**:
- `test_create_route_creates_deny_policy()`
- `test_hire_grants_access()`
- `test_unhire_revokes_access()`
- `test_multi_customer_access()`
- `test_delete_agent_with_customers_fails()`
- `test_delete_agent_cleans_up_resources()`

**Files to Create**:
- `backend/tests/test_gateway_rbac.py`

### 6. Logging & Monitoring
**Goal**: Add structured logging for security events.

**Implementation**:
1. Log all policy changes with customer ID and timestamp
2. Log access grants/revocations
3. Log failed access attempts (if gateway provides logs)
4. Add metrics for policy operations

**Acceptance Criteria**:
- All RBAC operations are logged
- Logs include customer ID, agent type, action, timestamp
- Logs are structured (JSON) for easy parsing

## Low Priority 🟢

### 7. Policy Validation
**Goal**: Add validation to ensure policies are correctly formatted.

**Implementation**:
1. Validate customer IDs are UUIDs
2. Validate CEL expressions are syntactically correct
3. Add pre-flight checks before applying policies
4. Add rollback on failure

### 8. Rate Limiting
**Goal**: Add per-customer rate limiting via TrafficPolicy.

**Research**:
- Check if kgateway supports rate limiting in TrafficPolicy
- Implement per-customer rate limits
- Add configuration for different tiers

### 9. Audit Trail
**Goal**: Store policy changes in database for audit.

**Implementation**:
1. Create `policy_audit` table
2. Record all grant/revoke operations
3. Add API endpoint to view audit log
4. Add admin UI to view policy history

### 10. Documentation
**Goal**: Complete user-facing documentation.

**Documents to Create**:
- Admin guide: How to manage agents and RBAC
- Customer guide: How hiring affects access
- Troubleshooting guide: Common RBAC issues
- API documentation: RBAC endpoints

## Testing Checklist

### Manual Testing
- [ ] Import new agent → verify route + deny-all policy created
- [ ] Hire agent → verify customer added to policy
- [ ] Chat with agent → verify success
- [ ] Unhire agent → verify customer removed, policy reverts to deny-all
- [ ] Try to chat after unhire → verify 403 (if possible to test)
- [ ] Multi-customer hire → verify both in policy
- [ ] Multi-customer unhire → verify correct customer removed
- [ ] Delete agent with customers → verify 400 error
- [ ] Delete agent without customers → verify cleanup

### Automated Testing
- [ ] Unit tests for `gateway_config_service`
- [ ] Integration tests for hire/unhire flows
- [ ] E2E tests for complete lifecycle
- [ ] Security tests for unauthorized access

## Success Criteria

The implementation is considered complete when:
1. ✅ All routes are secure by default
2. ✅ Customers can only access agents they've hired
3. ✅ Multi-tenant isolation is enforced
4. ✅ Access is immediately revoked on unhire
5. ⏳ Multi-customer scenarios work correctly
6. ⏳ Agents can be safely deleted
7. ⏳ Admin UI supports agent deletion
8. ⏳ All operations are logged
9. ⏳ Automated tests cover critical paths

## Timeline Estimate

- **High Priority Tasks**: 4-6 hours
- **Medium Priority Tasks**: 8-10 hours
- **Low Priority Tasks**: 12-16 hours
- **Total**: 24-32 hours

## Notes

- The core RBAC implementation is **complete and functional**
- Focus on high-priority tasks for production readiness
- Medium and low priority tasks can be done iteratively
- Consider creating a separate epic for monitoring/observability
