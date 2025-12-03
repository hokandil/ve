# Agent Gateway RBAC 403 Enforcement Test Script
# Tests that the Agent Gateway correctly enforces RBAC policies

Write-Host "=== Agent Gateway RBAC 403 Enforcement Tests ===" -ForegroundColor Cyan
Write-Host ""

# Configuration
$GATEWAY_URL = "http://localhost:8080"
$AGENT_TYPE = "wellness"
$AGENT_HOST = "$AGENT_TYPE.local"
$VALID_CUSTOMER_ID = "test-customer-uuid-123"  # Replace with actual customer ID from database
$INVALID_CUSTOMER_ID = "invalid-customer-uuid-999"

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Gateway URL: $GATEWAY_URL"
Write-Host "  Agent Type: $AGENT_TYPE"
Write-Host "  Agent Host: $AGENT_HOST"
Write-Host "  Valid Customer ID: $VALID_CUSTOMER_ID"
Write-Host ""

# Test 1: Request without X-Customer-ID header (should be 403)
Write-Host "[Test 1] Request WITHOUT X-Customer-ID header..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$GATEWAY_URL/chat" `
        -Method POST `
        -Headers @{"Host" = $AGENT_HOST} `
        -Body '{"message": "test"}' `
        -ContentType "application/json" `
        -ErrorAction Stop
    
    Write-Host "  ❌ FAIL: Expected 403, got $($response.StatusCode)" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 403) {
        Write-Host "  ✅ PASS: Got 403 Forbidden as expected" -ForegroundColor Green
    } else {
        Write-Host "  ❌ FAIL: Expected 403, got $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    }
}
Write-Host ""

# Test 2: Request with WRONG X-Customer-ID (should be 403)
Write-Host "[Test 2] Request with WRONG X-Customer-ID..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$GATEWAY_URL/chat" `
        -Method POST `
        -Headers @{
            "Host" = $AGENT_HOST
            "X-Customer-ID" = $INVALID_CUSTOMER_ID
        } `
        -Body '{"message": "test"}' `
        -ContentType "application/json" `
        -ErrorAction Stop
    
    Write-Host "  ❌ FAIL: Expected 403, got $($response.StatusCode)" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 403) {
        Write-Host "  ✅ PASS: Got 403 Forbidden as expected" -ForegroundColor Green
    } else {
        Write-Host "  ❌ FAIL: Expected 403, got $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    }
}
Write-Host ""

# Test 3: Request with CORRECT X-Customer-ID (should be 200 or 404 if agent not running)
Write-Host "[Test 3] Request with CORRECT X-Customer-ID..." -ForegroundColor Yellow
Write-Host "  NOTE: This test requires the customer to have hired the agent first" -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri "$GATEWAY_URL/chat" `
        -Method POST `
        -Headers @{
            "Host" = $AGENT_HOST
            "X-Customer-ID" = $VALID_CUSTOMER_ID
        } `
        -Body '{"message": "test"}' `
        -ContentType "application/json" `
        -ErrorAction Stop
    
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✅ PASS: Got 200 OK - Request was allowed" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  WARN: Got $($response.StatusCode) - Not 200 but also not 403" -ForegroundColor Yellow
    }
} catch {
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "  ⚠️  WARN: Got 404 - Agent might not be running, but RBAC allowed the request" -ForegroundColor Yellow
    } elseif ($_.Exception.Response.StatusCode -eq 403) {
        Write-Host "  ❌ FAIL: Got 403 - Customer should have access!" -ForegroundColor Red
        Write-Host "       Make sure customer $VALID_CUSTOMER_ID has hired the $AGENT_TYPE agent" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠️  WARN: Got $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
    }
}
Write-Host ""

# Test 4: Request with empty X-Customer-ID (should be 403)
Write-Host "[Test 4] Request with EMPTY X-Customer-ID..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$GATEWAY_URL/chat" `
        -Method POST `
        -Headers @{
            "Host" = $AGENT_HOST
            "X-Customer-ID" = ""
        } `
        -Body '{"message": "test"}' `
        -ContentType "application/json" `
        -ErrorAction Stop
    
    Write-Host "  ❌ FAIL: Expected 403, got $($response.StatusCode)" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 403) {
        Write-Host "  ✅ PASS: Got 403 Forbidden as expected" -ForegroundColor Green
    } else {
        Write-Host "  ❌ FAIL: Expected 403, got $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    }
}
Write-Host ""

Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Tests completed. Review results above." -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Ensure a customer has hired the $AGENT_TYPE agent in the database" -ForegroundColor Gray
Write-Host "2. Update VALID_CUSTOMER_ID in this script with the actual customer UUID" -ForegroundColor Gray
Write-Host "3. Verify the agent is deployed and accessible via the gateway" -ForegroundColor Gray
Write-Host "4. Run this script again to validate all scenarios" -ForegroundColor Gray
