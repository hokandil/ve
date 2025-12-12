# Test Temporal Workflow Execution
# This script submits a test task and monitors workflow execution

param(
    [string]$CustomerID = "test-customer-$(Get-Random -Maximum 9999)",
    [string]$TaskDescription = "Test Temporal workflow execution",
    [string]$ApiUrl = "http://localhost:8000"
)

Write-Host "Testing Temporal Workflow Execution" -ForegroundColor Green
Write-Host "====================================`n" -ForegroundColor Green

# Check if backend is running
try {
    $health = Invoke-RestMethod -Uri "$ApiUrl/health" -Method Get -ErrorAction Stop
    Write-Host "✅ Backend API is healthy" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend API is not accessible at $ApiUrl" -ForegroundColor Red
    Write-Host "   Please start the backend: docker-compose up -d backend" -ForegroundColor Yellow
    exit 1
}

# Check if Temporal UI is accessible
try {
    $temporal = Invoke-WebRequest -Uri "http://localhost:8080" -Method Get -ErrorAction Stop
    Write-Host "✅ Temporal UI is accessible" -ForegroundColor Green
} catch {
    Write-Host "❌ Temporal UI is not accessible at http://localhost:8080" -ForegroundColor Red
    Write-Host "   Please start Temporal: docker-compose up -d temporal temporal-ui" -ForegroundColor Yellow
    exit 1
}

Write-Host "`nSubmitting Test Task..." -ForegroundColor Cyan
Write-Host "  Customer ID: $CustomerID" -ForegroundColor White
Write-Host "  Description: $TaskDescription" -ForegroundColor White

# Submit task
$taskPayload = @{
    customer_id = $CustomerID
    title = "Test Task"
    description = $TaskDescription
    priority = "high"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$ApiUrl/api/tasks" `
        -Method Post `
        -ContentType "application/json" `
        -Body $taskPayload `
        -ErrorAction Stop
    
    Write-Host "`n✅ Task submitted successfully!" -ForegroundColor Green
    Write-Host "  Task ID: $($response.id)" -ForegroundColor White
    Write-Host "  Workflow ID: $($response.workflow_id)" -ForegroundColor White
    Write-Host "  Status: $($response.status)" -ForegroundColor White
    
    $taskId = $response.id
    $workflowId = $response.workflow_id
    
} catch {
    Write-Host "`n❌ Failed to submit task" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`nMonitoring Workflow Execution..." -ForegroundColor Cyan
Write-Host "  Open Temporal UI: http://localhost:8080" -ForegroundColor Yellow
Write-Host "  Search for workflow: $workflowId" -ForegroundColor Yellow

# Wait and check task status
Write-Host "`nWaiting for workflow to complete (30 seconds)..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

for ($i = 1; $i -le 6; $i++) {
    try {
        $taskStatus = Invoke-RestMethod -Uri "$ApiUrl/api/tasks/$taskId" -Method Get -ErrorAction Stop
        
        Write-Host "  [$i/6] Task Status: $($taskStatus.status)" -ForegroundColor White
        
        if ($taskStatus.status -eq "completed") {
            Write-Host "`n✅ Workflow completed successfully!" -ForegroundColor Green
            Write-Host "  Final Status: $($taskStatus.status)" -ForegroundColor White
            break
        } elseif ($taskStatus.status -eq "failed") {
            Write-Host "`n❌ Workflow failed" -ForegroundColor Red
            break
        }
        
        Start-Sleep -Seconds 5
    } catch {
        Write-Host "  [$i/6] Error checking status: $($_.Exception.Message)" -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    }
}

Write-Host "`nWorkflow Details:" -ForegroundColor Cyan
Write-Host "  View in Temporal UI: http://localhost:8080/namespaces/default/workflows/$workflowId" -ForegroundColor White

Write-Host "`nWorker Logs:" -ForegroundColor Cyan
Write-Host "  docker-compose logs temporal-worker --tail=20" -ForegroundColor White

Write-Host "`n✅ Test Complete!" -ForegroundColor Green
