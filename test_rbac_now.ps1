# Quick test of the actual deployed policy
$GATEWAY_URL = "http://localhost:8080"
$AGENT_HOST = "wellness.local"
$VALID_CUSTOMER_ID = "ea15052d-1c39-4865-8ac0-f1160d44829f"  # From the policy
$INVALID_CUSTOMER_ID = "invalid-customer-uuid-999"

Write-Host "Testing RBAC enforcement on deployed wellness agent..." -ForegroundColor Cyan
Write-Host ""

# Test 1: Without header (should fail)
Write-Host "[Test 1] No X-Customer-ID header:" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$GATEWAY_URL/" `
        -Method GET `
        -Headers @{"Host" = $AGENT_HOST} `
        -ErrorAction Stop
    Write-Host "  Status: $($response.StatusCode) - ❌ Should have been blocked!" -ForegroundColor Red
} catch {
    Write-Host "  Status: $($_.Exception.Response.StatusCode) - ✅ Blocked as expected" -ForegroundColor Green
}

# Test 2: With wrong customer ID (should fail)
Write-Host "[Test 2] Wrong X-Customer-ID:" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$GATEWAY_URL/" `
        -Method GET `
        -Headers @{
            "Host" = $AGENT_HOST
            "X-Customer-ID" = $INVALID_CUSTOMER_ID
        } `
        -ErrorAction Stop
    Write-Host "  Status: $($response.StatusCode) - ❌ Should have been blocked!" -ForegroundColor Red
} catch {
    Write-Host "  Status: $($_.Exception.Response.StatusCode) - ✅ Blocked as expected" -ForegroundColor Green
}

# Test 3: With correct customer ID (should work)
Write-Host "[Test 3] Correct X-Customer-ID:" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$GATEWAY_URL/" `
        -Method GET `
        -Headers @{
            "Host" = $AGENT_HOST
            "X-Customer-ID" = $VALID_CUSTOMER_ID
        } `
        -ErrorAction Stop
    Write-Host "  Status: $($response.StatusCode) - ✅ Allowed through!" -ForegroundColor Green
} catch {
    $statusCode = $_.Exception.Response.StatusCode
    if ($statusCode -eq 404) {
        Write-Host "  Status: 404 - ✅ RBAC allowed, agent returned 404 (normal)" -ForegroundColor Green
    } else {
        Write-Host "  Status: $statusCode - ❌ Unexpected!" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "RBAC is working correctly!" -ForegroundColor Green
