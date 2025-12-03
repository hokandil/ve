---
description: Secure Agent Gateway Integration with Multi-Tenant RBAC
---

# Secure Agent Gateway Integration Plan

## Objective
Ensure secure, multi-tenant access to shared agents via Agent Gateway (kgateway). Access must be "deny by default" and explicitly granted only to hired customers.

## Current Issues
1. **Open Access:** Agents are accessible via HTTPRoute without TrafficPolicy enforcement.
2. **Lifecycle Gaps:** Hire/Unhire flows are not correctly updating TrafficPolicies.
3. **Multi-Tenancy:** Behavior for multiple customers on the same agent is unverified.

## Implementation Tasks

### Phase 1: Debug & Fix RBAC Generation 🔴
- [ ] **1.1 Add Logging:** Enhance `gateway_config_service.py` with verbose logging for K8s API calls.
- [ ] **1.2 Fix `grant_customer_access`:** Debug why TrafficPolicy isn't being created. Check for:
    - K8s API permissions
    - Correct Group/Version/Kind for TrafficPolicy
    - Namespace issues
- [ ] **1.3 Verify Policy Structure:** Ensure the CEL expression correctly targets `request.headers['X-Customer-ID']`.

### Phase 2: Enforce Security 🔒
- [ ] **2.1 Default Deny:** Configure a global or namespace-level TrafficPolicy that denies all traffic to `*.local` unless explicitly allowed.
    - *Alternative:* Ensure specific TrafficPolicies use a "catch-all deny" if no match found (though kgateway usually denies if RBAC is enabled and no rule matches).
- [ ] **2.2 Validate Headers:** Ensure backend *always* sends `X-Customer-ID`.

### Phase 3: Multi-Tenant Lifecycle Management 🔄
- [ ] **3.1 Test Multi-Hire:**
    - Hire Agent X as Customer A -> Policy created with `[A]`.
    - Hire Agent X as Customer B -> Policy updated to `[A, B]`.
- [ ] **3.2 Test Partial Unhire:**
    - Unhire Customer A -> Policy updated to `[B]`.
    - Verify A gets 403, B gets 200.
- [ ] **3.3 Test Full Unhire:**
    - Unhire Customer B -> Policy deleted (or empty).
    - Verify both get 403.

### Phase 4: Admin Lifecycle 🛠️
- [ ] **4.1 Delete Agent:**
    - Admin deletes Agent X.
    - Ensure `HTTPRoute` AND `TrafficPolicy` are deleted.
    - Verify 404/503 for all requests.

## Verification Plan
1. **Pre-Hire:** `curl` to agent -> Expect 403.
2. **Post-Hire:** `curl` with valid ID -> Expect 200.
3. **Post-Unhire:** `curl` with old ID -> Expect 403.
