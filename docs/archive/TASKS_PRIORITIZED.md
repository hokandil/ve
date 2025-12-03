# VE SaaS Platform - Prioritized Task List
## Updated: November 30, 2025

---

## 🔴 CRITICAL - Complete This Week (Agent Gateway RBAC)

### 1. Multi-Customer RBAC Testing
**Priority:** P0 - Blocker for production  
**Effort:** 4 hours  
**Owner:** Backend  

**Tasks:**
- [ ] Create second test customer account in Supabase
- [ ] Customer A hires `wellness` agent
- [ ] Verify TrafficPolicy created with Customer A's UUID
- [ ] Customer B hires same `wellness` agent
- [ ] Verify TrafficPolicy updated to include both UUIDs
- [ ] Test Customer A chat → should work (200)
- [ ] Test Customer B chat → should work (200)
- [ ] Customer A unhires
- [ ] Verify TrafficPolicy only contains Customer B
- [ ] Test Customer A chat → should fail (403 or blocked)
- [ ] Test Customer B chat → should still work (200)
- [ ] Document test results

**Acceptance Criteria:**
- Multiple customers can hire the same agent
- TrafficPolicy correctly maintains all customer UUIDs
- Unhiring one customer doesn't affect others
- Access is immediately revoked on unhire

**Files:**
- `backend/tests/test_rbac_multi_customer.py` (new)
- `docs/agent_gateway_rbac_test_results.md` (new)

---

### 2. Delete Agent Protection
**Priority:** P0 - Data safety  
**Effort:** 2 hours  
**Owner:** Backend  

**Tasks:**
- [ ] Test delete agent with active customers
  - Should return 400 with clear error message
  - Should list number of customers using it
- [ ] Test delete agent with no customers
  - Should return 200
  - Should delete HTTPRoute
  - Should delete TrafficPolicy
  - Should delete database record
- [ ] Verify no orphaned resources in Kubernetes
- [ ] Add logging for delete operations
- [ ] Document delete flow

**Acceptance Criteria:**
- Cannot delete agents with active customers
- Can delete agents with no customers
- All resources cleaned up properly
- Clear error messages

**Files:**
- Already implemented in `backend/app/api/discovery.py`
- Test in `backend/tests/test_agent_deletion.py` (new)

---

### 3. Admin UI - Delete Agent Button
**Priority:** P0 - Required for agent management  
**Effort:** 3 hours  
**Owner:** Frontend (Admin)  

**Tasks:**
- [ ] Add "Delete" button to Marketplace page agent cards
- [ ] Create confirmation dialog component
  - Show agent name
  - Show warning about permanent deletion
  - Require explicit confirmation
- [ ] Call `DELETE /api/discovery/agents/{ve_id}` endpoint
- [ ] Handle 400 error (customers still using)
  - Show error toast with customer count
  - Suggest unhiring first
- [ ] Handle 200 success
  - Show success toast
  - Remove agent from list
  - Refresh marketplace data
- [ ] Add loading state during deletion
- [ ] Add error handling for network failures

**Acceptance Criteria:**
- Admin can delete agents from UI
- Clear confirmation before delete
- Helpful error messages
- UI updates immediately

**Files:**
- `admin-frontend/src/pages/Marketplace.tsx` (modify)
- `admin-frontend/src/components/DeleteAgentDialog.tsx` (new)
- `admin-frontend/src/hooks/useDeleteAgent.ts` (new)

---

### 4. Automated RBAC Tests
**Priority:** P1 - Prevent regressions  
**Effort:** 6 hours  
**Owner:** Backend  

**Tasks:**
- [ ] Set up pytest fixtures for test environment
- [ ] Write test: `test_create_route_creates_deny_policy()`
  - Import agent
  - Verify HTTPRoute created
  - Verify TrafficPolicy created with deny-all
- [ ] Write test: `test_hire_grants_access()`
  - Hire agent as customer
  - Verify customer UUID in TrafficPolicy
- [ ] Write test: `test_unhire_revokes_access()`
  - Unhire agent
  - Verify customer UUID removed
  - Verify policy reverts to deny-all
- [ ] Write test: `test_multi_customer_access()`
  - Two customers hire same agent
  - Verify both in policy
  - One unhires
  - Verify only one remains
- [ ] Write test: `test_delete_agent_with_customers_fails()`
  - Customer hires agent
  - Attempt delete
  - Verify 400 error
- [ ] Write test: `test_delete_agent_cleans_up_resources()`
  - Delete agent with no customers
  - Verify HTTPRoute deleted
  - Verify TrafficPolicy deleted
  - Verify database record deleted
- [ ] Add CI integration (GitHub Actions)

**Acceptance Criteria:**
- 90%+ test coverage for RBAC flows
- All tests pass
- Tests run in CI
- Clear test documentation

**Files:**
- `backend/tests/test_gateway_rbac.py` (new)
- `backend/tests/conftest.py` (update fixtures)
- `.github/workflows/test.yml` (update)

---

### 5. RBAC Logging & Monitoring
**Priority:** P1 - Security audit trail  
**Effort:** 4 hours  
**Owner:** Backend  

**Tasks:**
- [ ] Add structured logging to `gateway_config_service.py`
  - Log policy creation with agent type, timestamp
  - Log access grants with customer ID, agent type, timestamp
  - Log access revocations with customer ID, agent type, timestamp
  - Log policy deletions with agent type, timestamp
- [ ] Add security event logging
  - Log failed access attempts (if detectable)
  - Log policy modification failures
- [ ] Add metrics collection
  - Count of active policies
  - Count of customers per agent
  - Policy operation latency
- [ ] Create logging documentation
  - Log format specification
  - Log levels
  - Log retention policy

**Acceptance Criteria:**
- All RBAC operations are logged
- Logs are structured (JSON)
- Logs include all relevant context
- Logs are easily searchable

**Files:**
- `backend/app/services/gateway_config_service.py` (enhance)
- `backend/app/core/logging_config.py` (new)
- `docs/logging_specification.md` (new)

---

## 🟡 HIGH PRIORITY - Complete Next Week (Chat Interface)

### 6. SSE Streaming Support
**Priority:** P1 - Better UX  
**Effort:** 8 hours  
**Owner:** Backend + Frontend  

**Backend Tasks:**
- [ ] Create SSE endpoint `/api/messages/ves/{id}/chat/stream`
- [ ] Implement EventSource response
- [ ] Parse A2A SSE events correctly
- [ ] Handle task_status_update events
- [ ] Handle task_artifact_update events
- [ ] Send incremental updates to client
- [ ] Handle connection errors

**Frontend Tasks:**
- [ ] Implement EventSource client in `useChat.ts`
- [ ] Update UI in real-time as messages arrive
- [ ] Show typing indicator
- [ ] Handle connection errors
- [ ] Implement reconnection logic

**Acceptance Criteria:**
- Real-time streaming responses
- Smooth UX with no lag
- Proper error handling

**Files:**
- `backend/app/api/messages.py` (add SSE endpoint)
- `frontend/src/hooks/useChat.ts` (add EventSource)
- `frontend/src/components/chat/ChatMessage.tsx` (update)

---

### 7. Enhanced Chat UI
**Priority:** P1 - Core feature  
**Effort:** 6 hours  
**Owner:** Frontend  

**Tasks:**
- [ ] Redesign Chat page with modern UI
- [ ] Add message bubbles (user vs agent)
- [ ] Add timestamps
- [ ] Add typing indicators
- [ ] Add auto-scroll to latest message
- [ ] Add markdown rendering
- [ ] Add code syntax highlighting
- [ ] Add loading states
- [ ] Add error states
- [ ] Make responsive for mobile

**Acceptance Criteria:**
- Professional chat experience
- Clear visual distinction between user/agent
- Rich content display
- Mobile-friendly

**Files:**
- `frontend/src/pages/Chat.tsx` (redesign)
- `frontend/src/components/chat/MessageBubble.tsx` (new)
- `frontend/src/components/chat/ChatInput.tsx` (new)
- `frontend/src/components/chat/TypingIndicator.tsx` (new)

---

### 8. Customer UI - Agent Status Indicators
**Priority:** P2 - Nice to have  
**Effort:** 2 hours  
**Owner:** Frontend  

**Tasks:**
- [ ] Add "Active" badge to hired agents in My Team
- [ ] Add "Locked" state for unhired agents
- [ ] Add tooltips explaining access control
- [ ] Add visual feedback on hire/unhire
- [ ] Update agent cards with status colors

**Acceptance Criteria:**
- Clear visual feedback on access status
- Helpful tooltips
- Consistent design

**Files:**
- `frontend/src/pages/MyTeam.tsx` (update)
- `frontend/src/components/AgentStatusBadge.tsx` (new)

---

## 🟢 MEDIUM PRIORITY - Complete in 2-3 Weeks

### 9. KAgent Deployment Service
**Priority:** P2  
**Effort:** 12 hours  

**Tasks:**
- [ ] Implement `KAgentDeploymentService`
- [ ] Deploy Agent CRDs to Kubernetes
- [ ] Monitor deployment status
- [ ] Handle deployment failures
- [ ] Update database with deployment info

**Files:**
- `backend/app/services/kagent_deployment_service.py` (new)

---

### 10. Agent Health Monitoring
**Priority:** P2  
**Effort:** 8 hours  

**Tasks:**
- [ ] Poll agent status from KAgent
- [ ] Update database with health status
- [ ] Send alerts on failures
- [ ] Create health dashboard

**Files:**
- `backend/app/services/kagent_health_service.py` (new)
- `admin-frontend/src/pages/AgentHealth.tsx` (new)

---

## 📊 Task Summary

### This Week (Critical)
- **Total Tasks:** 5
- **Estimated Effort:** 19 hours
- **Focus:** Agent Gateway RBAC completion

### Next Week (High Priority)
- **Total Tasks:** 3
- **Estimated Effort:** 16 hours
- **Focus:** Chat interface enhancement

### Next 2-3 Weeks (Medium Priority)
- **Total Tasks:** 2
- **Estimated Effort:** 20 hours
- **Focus:** KAgent integration

---

## 🎯 Success Metrics

### Week 1 Goals
- [ ] Multi-customer RBAC tested and verified
- [ ] Delete protection working
- [ ] Admin can delete agents from UI
- [ ] 90%+ test coverage for RBAC
- [ ] All RBAC operations logged

### Week 2 Goals
- [ ] Real-time chat with SSE
- [ ] Modern chat UI
- [ ] Agent status indicators

### Week 3 Goals
- [ ] KAgent deployment working
- [ ] Agent health monitoring
- [ ] Production-ready platform

---

## 🚨 Blockers & Risks

### Current Blockers
- None

### Potential Risks
1. **Multi-tenant testing complexity** - Mitigated by creating test accounts
2. **SSE browser compatibility** - Mitigated by fallback to polling
3. **Kubernetes permissions** - Mitigated by proper RBAC setup

---

## 📝 Notes

- Focus on completing Week 1 tasks before moving to Week 2
- All tasks have clear acceptance criteria
- Estimated efforts are conservative
- Can parallelize frontend and backend work
- Regular testing after each task completion

---

**Last Updated:** November 30, 2025  
**Next Review:** December 2, 2025 (after Week 1 completion)
