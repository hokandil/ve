# Documentation Cleanup Script
# This script moves outdated documentation to the archive folder

Write-Host "VE SaaS Platform - Documentation Cleanup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Files to archive
$filesToArchive = @(
    "IMPLEMENTATION_PLAN_v2.md",
    "IMPLEMENTATION.md",
    "BACKEND_TASKS_COMPLETE.md",
    "FRONTEND_TASKS_COMPLETE.md",
    "FRONTEND_TASKS_COMPLETED.md",
    "ARCHITECTURE_CHANGE_SUMMARY.md",
    "ARCHITECTURE_DECISION_FINAL.md",
    "ADMIN_CORRECTION_SUMMARY.md",
    "ADMIN_FRONTEND_FIX.md",
    "MIGRATION_FIX.md",
    "COMPLIANCE_ANALYSIS.md",
    "ve_saas_prd.md",
    "PRD_v2_SIMPLIFIED.md",
    "ve-admin-creator-interface.md"
)

$archivePath = "docs\archive"
$movedCount = 0
$notFoundCount = 0

Write-Host "Moving outdated documentation to $archivePath..." -ForegroundColor Yellow
Write-Host ""

foreach ($file in $filesToArchive) {
    if (Test-Path $file) {
        Write-Host "  Moving: $file" -ForegroundColor Green
        Move-Item -Path $file -Destination $archivePath -Force
        $movedCount++
    } else {
        Write-Host "  Not found: $file" -ForegroundColor Gray
        $notFoundCount++
    }
}

Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Moved: $movedCount files" -ForegroundColor Green
Write-Host "  Not found: $notFoundCount files" -ForegroundColor Gray
Write-Host ""

# Optional: Clean up test files
Write-Host "Optional cleanup (test files):" -ForegroundColor Yellow
Write-Host "  The following files can be moved to a tests/ folder:" -ForegroundColor Gray
Write-Host "    - check_api.py" -ForegroundColor Gray
Write-Host "    - test_hire.py" -ForegroundColor Gray
Write-Host "    - test_methods.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  Run this to move them:" -ForegroundColor Gray
Write-Host "    New-Item -ItemType Directory -Force -Path tests" -ForegroundColor DarkGray
Write-Host "    Move-Item -Path check_api.py,test_hire.py,test_methods.py -Destination tests -Force" -ForegroundColor DarkGray
Write-Host ""

# Optional: Clean up temp files
Write-Host "Optional cleanup (temp files):" -ForegroundColor Yellow
Write-Host "  The following files might be temporary:" -ForegroundColor Gray
Write-Host "    - temp_openapi.json" -ForegroundColor Gray
Write-Host "    - package-lock.json (if not needed in root)" -ForegroundColor Gray
Write-Host ""
Write-Host "  Review and delete if not needed." -ForegroundColor Gray
Write-Host ""

Write-Host "Documentation cleanup complete!" -ForegroundColor Green
Write-Host "See DOCUMENTATION_INDEX.md for the new structure." -ForegroundColor Cyan
