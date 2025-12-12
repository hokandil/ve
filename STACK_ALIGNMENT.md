# Stack Alignment Plan: Lean & Unified

This document outlines the migration plan to align the current Virtual Employee platform with the target "Lean & Unified" architecture.

## Target Architecture Overview

| Component | Solution | Role | Replaces Current |
|-----------|----------|------|------------------|
| **Frontend** | React | UI | N/A (Existing) |
| **API** | FastAPI | Routes, Validation, Middleware | N/A (Existing) |
| **Real-Time** | **Centrifugo** | WebSocket, Presence, History | SSE (Server-Sent Events) |
| **Database** | Postgres (Supabase) | Data Persistence | N/A (Existing) |
| **Async Tasks** | **Celery** | Workers, Retries, KAgent Ops | Direct Async/Background Tasks |
| **Caching** | Redis | Cache, Queue (Celery), Pub/Sub | Redis (Caching only) |
| **Observability** | **OpenObserve** | Logs, Metrics, Traces, Alerts | Jaeger, OTel Console |

## Gap Analysis & Migration Steps

### 1. Observability: OpenObserve
**Current:** OpenTelemetry exporting to Jaeger (traces) and Console (logs).
**Target:** OpenTelemetry exporting to OpenObserve (traces, logs, metrics).
**Action Items:**
- [ ] Sign up/Deploy OpenObserve (or use cloud).
- [ ] Configure OpenTelemetry OTLP exporter to point to OpenObserve endpoint.
- [ ] Update `telemetry.py` to send logs and metrics to OpenObserve.
- [ ] Create basic dashboard in OpenObserve.

### 2. Async Tasks: Celery
**Current:** `orchestrator.py` uses `async/await` and `BackgroundTasks` for agent invocation.
**Target:** Celery workers handling agent orchestration and long-running tasks.
**Action Items:**
- [ ] Install `celery` and `redis` (as broker).
- [ ] Configure Celery app in `backend/app/core/celery_app.py`.
- [ ] Refactor `route_request_to_orchestrator` to dispatch Celery tasks.
- [ ] Refactor `invoke_agent` to run within Celery workers.
- [ ] Implement retry logic using Celery's built-in retry mechanism.

### 3. Real-Time: Centrifugo
**Current:** `invoke_agent_stream` uses Server-Sent Events (SSE) via `httpx` stream.
**Target:** Centrifugo for bi-directional real-time communication.
**Action Items:**
- [ ] Deploy Centrifugo (Docker/Binary).
- [ ] Install `cent` (Python client) or use HTTP API.
- [ ] Update Frontend to use `centrifuge-js`.
- [ ] Replace SSE endpoints with Centrifugo publish calls.
- [ ] Implement channel presence for "Agent Typing" indicators.

### 4. Resilience: Middleware
**Current:** Basic error handling.
**Target:** Robust middleware for Rate Limiting and Circuit Breaking.
**Action Items:**
- [ ] Implement Rate Limiting middleware (e.g., `slowapi`).
- [ ] Implement Circuit Breaker pattern for external calls (Agent Gateway).

## Implementation Priority

1.  **Observability (OpenObserve)**: Easiest to implement and provides immediate visibility for the rest of the migration.
2.  **Async Tasks (Celery)**: Critical for reliability and scaling agent orchestration.
3.  **Real-Time (Centrifugo)**: Enhances user experience and replaces the fragile SSE implementation.
4.  **Resilience**: Ongoing hardening.

## Next Steps
Please select a component to start the migration. Recommended: **Observability (OpenObserve)** or **Async Tasks (Celery)**.
