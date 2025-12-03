---
description: Complete Agent Gateway Integration with proper routing and RBAC
---

# Agent Gateway Integration - Task Plan

## Current State (Updated: November 30, 2025)
- ✅ Agent Gateway deployed and accessible
- ✅ A2A protocol discovered (`message/stream` method)
- ✅ SSE response parsing implemented
- ✅ `gateway_config_service.py` created with route/policy management
- ✅ `agent_gateway_service.py` updated with correct protocol
- ✅ Import endpoint updated to create HTTPRoute
- ✅ **TrafficPolicy RBAC implemented and tested (basic flow)**
- ✅ **Secure by Default architecture implemented**
- ✅ **Hire/Unhire lifecycle working**
- ⚠️ Multi-customer scenario needs testing
- ⚠️ Delete agent endpoint needs frontend integration

## Tasks

### Phase 1: Verify Current Implementation ✅ COMPLETE

- [x] 1.1 Test agent communication works
  - Agent responds to messages
  - SSE streaming works
  - Response parsing extracts text correctly

- [x] 1.2 Verify HTTPRoute creation on import
  - Import agent via admin frontend
  - Check HTTPRoute created: `kubectl get httproute -n default`
  - Verify hostname routing configured

### Phase 2: Implement Complete RBAC Flow ✅ MOSTLY COMPLETE

- [x] 2.1 Test TrafficPolicy creation on hire
  - ✅ Customer hires agent
  - ✅ Verify TrafficPolicy created: `kubectl get trafficpolicy -n kgateway-system`
  - ✅ Check CEL expression includes customer ID
  - ✅ Verify customer can chat with agent
  - **Status:** Working - TrafficPolicy created with customer UUID

- [ ] 2.2 Test multi-customer access ⚠️ NEEDS TESTING
  - Different customer hires same agent
  - Verify TrafficPolicy updated (not recreated)
  - Check both customers in CEL expression
  - Verify both customers can chat
  - **Status:** Code implemented, needs manual testing

- [x] 2.3 Test access revocation on unhire
  - ✅ Customer unhires agent
  - ✅ Verify TrafficPolicy updated to remove customer
  - ✅ Policy reverts to deny-all (not deleted)
  - ⚠️ Need to verify customer gets 403 when trying to chat
  - **Status:** Backend working, 403 enforcement needs verification

- [x] 2.4 Test route deletion on agent delete
  - ✅ Admin deletes agent from marketplace (backend endpoint exists)
  - ✅ Verify TrafficPolicy deleted
  - ✅ Verify HTTPRoute deleted
  - ⏳ Frontend delete button not yet implemented
  - **Status:** Backend complete, frontend pending

### Phase 3: Handle Edge Cases ⏳ PARTIALLY COMPLETE

- [x] 3.1 Handle import of already-imported agent
  - ✅ Try importing same agent twice
  - ✅ Should skip HTTPRoute creation (409 conflict)
  - ✅ Should not fail the import
  - **Status:** Handled in `create_agent_route()`

- [x] 3.2 Handle hire when route doesn't exist
  - ✅ `grant_customer_access()` creates policy if missing
  - ✅ Fallback logic implemented
  - **Status:** Handled gracefully

- [x] 3.3 Handle Kubernetes unavailable
  - ✅ Checks `k8s_available` flag
  - ✅ Logs error but doesn't crash
  - ✅ Returns skip status
  - **Status:** Handled in all service methods

- [ ] 3.4 Handle agent service not found
  - Create HTTPRoute for non-existent service
  - Try to chat
  - Should return appropriate error
  - **Status:** Not yet tested

### Phase 4: Add Delete Agent Endpoint ✅ BACKEND COMPLETE

- [x] 4.1 Create DELETE endpoint in admin API
  - ✅ `DELETE /api/discovery/agents/{ve_id}` implemented
  - ✅ Deletes from database
  - ✅ Calls `gateway_config.delete_agent_route()`
  - ✅ Prevents deletion if customers are using it
  - **Status:** Complete in `backend/app/api/discovery.py`

- [ ] 4.2 Wire up to admin frontend ⏳ PENDING
  - Add delete button in Marketplace page
  - Confirm dialog
  - Call delete endpoint
  - Refresh list on success
  - **Status:** Not yet implemented

### Phase 5: Monitoring & Logging ✅ COMPLETE

- [x] 5.1 Add structured logging
  - ✅ Log HTTPRoute creation/deletion
  - ✅ Log TrafficPolicy updates
  - ✅ Log customer access grants/revocations
  - ✅ Include agent_type and customer_id in logs
  - **Status:** Comprehensive logging added to `gateway_config_service.py`

- [x] 5.2 Add error handling
  - ✅ Catch Kubernetes API errors
  - ✅ Return user-friendly messages
  - ✅ Log technical details for debugging
  - **Status:** Error handling in all service methods

- [ ] 5.3 Add metrics (optional) ⏳ FUTURE
  - Count routes created/deleted
  - Count access grants/revocations
  - Track 403 errors (unauthorized access)
  - **Status:** Deferred to future enhancement

### Phase 6: Documentation ✅ COMPLETE

- [x] 6.1 Update implementation plan
  - ✅ Document Agent Gateway architecture
  - ✅ Update task completion status
  - ✅ Add troubleshooting section
  - **Status:** Created comprehensive docs

- [x] 6.2 Create admin guide
  - ✅ How to import agents
  - ✅ How to monitor routes
  - ✅ How to troubleshoot access issues
  - **Status:** Documented in `docs/agent_gateway_rbac_summary.md`

- [x] 6.3 Create developer guide
  - ✅ Agent Gateway architecture diagram
  - ✅ HTTPRoute and TrafficPolicy examples
  - ✅ Common debugging commands
  - **Status:** Created `docs/agent_gateway_architecture.md`

### Phase 7: Testing & Validation ⏳ PARTIALLY COMPLETE

- [ ] 7.1 End-to-end test ⚠️ NEEDS COMPLETION
  - [x] Import agent
  - [x] Hire as customer A
  - [x] Chat as customer A (should work) ✅
  - [ ] Hire as customer B
  - [ ] Chat as customer B (should work)
  - [x] Unhire as customer A
  - [ ] Chat as customer A (should fail) - needs verification
  - [ ] Chat as customer B (should still work)
  - [ ] Delete agent
  - [ ] Chat as customer B (should fail)
  - **Status:** Basic flow tested, multi-customer needs testing

- [ ] 7.2 Security test ⏳ NEEDS TESTING
  - Try to chat without X-Customer-ID header
  - Try to chat with wrong customer ID
  - Try to chat after unhiring
  - All should return 403
  - **Status:** Backend sends header, gateway enforcement needs verification

- [ ] 7.3 Performance test ⏳ FUTURE
  - Import 10 agents
  - Hire all as same customer
  - Verify all routes work
  - Check TrafficPolicy size (CEL expression)
  - **Status:** Deferred to future testing

## Verification Commands

```bash
# Check HTTPRoutes
kubectl get httproute -n default -l app=ve-platform

# Check TrafficPolicies
kubectl get trafficpolicy -n kgateway-system -l app=ve-platform

# View HTTPRoute details
kubectl get httproute agent-wellness -n default -o yaml

# View TrafficPolicy details
kubectl get trafficpolicy rbac-wellness -n kgateway-system -o yaml

# Check Agent Gateway logs
kubectl logs -n kgateway-system -l app=agent-gateway --tail=100

# Test route directly (with customer ID)
curl -v http://localhost:8080/ \
  -H "Host: wellness.local" \
  -H "X-Customer-ID: ea15052d-1c39-4865-8ac0-f1160d44829f" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"message/stream","params":{"message":{"kind":"message","parts":[{"kind":"text","text":"hi"}]}},"id":"1"}'

# Test route without customer ID (should fail)
curl -v http://localhost:8080/ \
  -H "Host: wellness.local" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"message/stream","params":{"message":{"kind":"message","parts":[{"kind":"text","text":"hi"}]}},"id":"1"}'
```

## Success Criteria

- ✅ Admin can import agents → HTTPRoute created
- ✅ Customer can hire agents → TrafficPolicy grants access
- ✅ Customer can chat with hired agents → Messages work
- ⚠️ Customer cannot chat with non-hired agents → 403 Forbidden (needs verification)
- ✅ Customer unhire removes access → Policy reverts to deny-all
- ⏳ Admin delete removes all routes → Backend done, frontend pending
- ⚠️ Multiple customers can share same agent → Code done, needs testing
- ✅ All operations logged properly
- ✅ Errors handled gracefully

## Overall Progress: 85% Complete ✅

### ✅ Completed (85%)
- Core RBAC implementation
- Secure by Default architecture
- HTTPRoute and TrafficPolicy management
- Hire/Unhire lifecycle
- Delete agent backend endpoint
- Comprehensive logging
- Error handling
- Documentation

### ⏳ Remaining (15%)
- Multi-customer testing
- 403 enforcement verification
- Delete agent frontend UI
- Security testing (curl tests)
- Automated test suite

## Next Immediate Steps

1. ⚠️ **Test multi-customer scenario** (2-3 hours)
   - Create second customer account
   - Test both customers hiring same agent
   - Verify TrafficPolicy contains both UUIDs

2. ⚠️ **Verify 403 enforcement** (1-2 hours)
   - Test chat without X-Customer-ID header
   - Test chat with wrong customer ID
   - Test chat after unhiring

3. ⏳ **Add delete agent UI** (2-3 hours)
   - Add delete button to admin frontend
   - Wire up to DELETE endpoint
   - Handle errors gracefully

4. ⏳ **Write automated tests** (4-6 hours)
   - pytest tests for RBAC flows
   - Integration tests
   - CI integration

5. ⏳ **Complete end-to-end test** (2-3 hours)
   - Full lifecycle test with multiple customers
   - Document test results

**Estimated Time to 100% Completion:** 12-18 hours

---

**Last Updated:** November 30, 2025  
**Status:** 🟢 85% Complete - Production Ready (pending final testing)  
**Blocker:** None  
**Next Review:** After multi-customer testing
