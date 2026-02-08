#!/usr/bin/env pwsh
# PowerShell demo for pipeline orchestration endpoint

$BaseUrl = "http://localhost:8000/api/v1"
$ApiUrl = "http://localhost:8000"

Write-Host ""
Write-Host "="*80 -ForegroundColor Green
Write-Host "  Pipeline Orchestration Endpoint - Demo" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Green
Write-Host ""

# Check if API is running
Write-Host "Checking API..." -ForegroundColor Cyan
try {
    $null = Invoke-WebRequest -Uri "$ApiUrl/docs" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "✅ API is running" -ForegroundColor Green
} catch {
    Write-Host "❌ API not responding" -ForegroundColor Red
    Write-Host "Start it with: python -m uvicorn app.main:app --reload" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "Select demo:" -ForegroundColor Cyan
Write-Host "  1 - Basic (3 routers, 1 switch)"
Write-Host "  2 - Medium (5 routers, 3 switches)"
Write-Host "  3 - Large (8 routers, 4 switches)"
Write-Host "  4 - Fast (skip analysis)"
Write-Host "  5 - Open API docs"
Write-Host "  0 - Exit"
Write-Host ""

$choice = Read-Host "Enter choice"

if ($choice -eq "0") {
    Write-Host "Goodbye! 👋"
    exit
}

if ($choice -eq "5") {
    Start-Process "$ApiUrl/docs"
    exit
}

$demos = @{
    "1" = @{ name="basic"; routers=3; switches=1; analysis=$true; seed=$null }
    "2" = @{ name="medium"; routers=5; switches=3; analysis=$true; seed=42 }
    "3" = @{ name="large"; routers=8; switches=4; analysis=$true; seed=123 }
    "4" = @{ name="fast"; routers=3; switches=1; analysis=$false; seed=$null }
}

if (-not $demos.ContainsKey($choice)) {
    Write-Host "Invalid choice" -ForegroundColor Red
    exit 1
}

$demo = $demos[$choice]
$payload = @{
    topology_name = "demo-$($demo.name)"
    num_routers = $demo.routers
    num_switches = $demo.switches
    run_analysis = $demo.analysis
}
if ($demo.seed) { $payload["seed"] = $demo.seed }

Write-Host ""
Write-Host "="*80 -ForegroundColor Cyan
Write-Host "  DEMO: $($demo.name.ToUpper())" -ForegroundColor Cyan
Write-Host "="*80 -ForegroundColor Cyan
Write-Host ""

Write-Host "Sending request..." -ForegroundColor Yellow
$start = Get-Date

try {
    $response = Invoke-RestMethod `
        -Uri "$BaseUrl/run-pipeline" `
        -Method POST `
        -Headers @{'Content-Type'='application/json'} `
        -Body ($payload | ConvertTo-Json)
    
    Write-Host ""
    Write-Host "✅ SUCCESS" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Results:" -ForegroundColor Cyan
    Write-Host "  Pipeline ID: $($response.pipeline_id)"
    Write-Host "  Status: $($response.overall_status)"
    Write-Host "  Duration: $("{0:N2}" -f $response.total_duration_seconds)s"
    Write-Host ""
    
    $s = $response.summary
    Write-Host "Topology:" -ForegroundColor Cyan
    Write-Host "  Name: $($s.topology_name)"
    Write-Host "  Devices: $($s.total_devices) ($($s.num_routers)R, $($s.num_switches)S)"
    Write-Host "  Links: $($s.total_links)"
    Write-Host ""
    
    if ($s.analysis_health_score) {
        Write-Host "Analysis:" -ForegroundColor Cyan
        Write-Host "  Health: $($s.analysis_health_score)/100"
        Write-Host "  Issues: $($s.analysis_issues_found)"
        Write-Host ""
    }
    
    Write-Host "Stages:" -ForegroundColor Cyan
    foreach ($stage in $response.stages.PSObject.Properties) {
        $st = $stage.Value
        $icon = if ($st.status -eq "success") { "✅" } else { "❌" }
        Write-Host "  $icon $($stage.Name.PadRight(25)) $("{0:N3}" -f $st.duration_seconds)s"
    }
    
} catch {
    Write-Host "❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
