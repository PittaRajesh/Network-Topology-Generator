# Quick demo script for PowerShell
# Run: .\demo.ps1

param(
    [string]$DemoType = "interactive"
)

$BaseUrl = "http://localhost:8000/api/v1"
$ApiUrl = "http://localhost:8000"

# Color output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Error { Write-Host "❌ $args" -ForegroundColor Red }
function Write-Info { Write-Host "ℹ️  $args" -ForegroundColor Blue }
function Write-Warning { Write-Host "⚠️  $args" -ForegroundColor Yellow }

# Demo payloads
$DemoPayloads = @{
    "basic" = @{
        topology_name = "demo-basic"
        num_routers = 3
        num_switches = 1
        run_analysis = $true
    }
    "medium" = @{
        topology_name = "demo-medium"
        num_routers = 5
        num_switches = 3
        seed = 42
        run_analysis = $true
    }
    "large" = @{
        topology_name = "demo-large"
        num_routers = 8
        num_switches = 4
        seed = 123
        run_analysis = $true
    }
    "fast" = @{
        topology_name = "demo-fast"
        num_routers = 3
        num_switches = 1
        run_analysis = $false
    }
}

function Check-ApiRunning {
    Write-Info "Checking if API is running..."
    try {
        $response = Invoke-WebRequest -Uri "$ApiUrl/docs" -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Success "API is running and accessible"
            return $true
        }
    }
    catch {
        Write-Error "Cannot reach API at $ApiUrl"
        Write-Host ""
        Write-Host "Please start the API first:" -ForegroundColor Cyan
        Write-Host "  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Cyan
        Write-Host ""
        return $false
    }
}

function Run-Pipeline {
    param(
        [hashtable]$Payload,
        [string]$DemoName
    )
    
    Write-Host ""
    Write-Host ("=" * 80) -ForegroundColor Cyan
    Write-Host "  DEMO: $($DemoName.ToUpper())" -ForegroundColor Cyan
    Write-Host ("=" * 80) -ForegroundColor Cyan
    Write-Host ""
    
    Write-Info "Request Payload:"
    Write-Host ($Payload | ConvertTo-Json -Depth 10) -ForegroundColor DarkGray
    Write-Host ""
    
    try {
        Write-Info "Executing pipeline..."
        $start = Get-Date
        
        $response = Invoke-RestMethod `
            -Uri "$BaseUrl/run-pipeline" `
            -Method POST `
            -Headers @{'Content-Type' = 'application/json'} `
            -Body ($Payload | ConvertTo-Json) `
            -TimeoutSec 60
        
        $elapsed = ((Get-Date) - $start).TotalSeconds
        
        Write-Success "Pipeline Execution Successful!"
        Write-Host ""
        
        # Display results
        Write-Host "📋 Execution Details:" -ForegroundColor Cyan
        Write-Host "   Pipeline ID: $($response.pipeline_id)"
        Write-Host "   Status: $($response.overall_status)"
        Write-Host "   Total Duration: $("{0:N2}" -f $response.total_duration_seconds)s"
        Write-Host ""
        
        $summary = $response.summary
        Write-Host "📊 Generated Topology:" -ForegroundColor Cyan
        Write-Host "   Name: $($summary.topology_name)"
        Write-Host "   Total Devices: $($summary.total_devices)"
        Write-Host "   Total Links: $($summary.total_links)"
        Write-Host "   Routers: $($summary.num_routers)"
        Write-Host "   Switches: $($summary.num_switches)"
        Write-Host "   Containerlab Nodes: $($summary.containerlab_nodes)"
        Write-Host ""
        
        if ($summary.analysis_health_score) {
            Write-Host "🔍 Topology Analysis:" -ForegroundColor Cyan
            Write-Host "   Health Score: $($summary.analysis_health_score)/100"
            Write-Host "   Issues Found: $($summary.analysis_issues_found)"
            Write-Host ""
        }
        
        Write-Host "⚙️  Pipeline Stages:" -ForegroundColor Cyan
        foreach ($stage in $response.stages.PSObject.Properties) {
            $stage_obj = $stage.Value
            $icon = if ($stage_obj.status -eq "success") { "✅" } else { "❌" }
            $duration = "{0:F4}s" -f $stage_obj.duration_seconds
            Write-Host "   $icon $($stage.Name.PadRight(30, ' ')) $duration"
            if ($stage_obj.error_message) {
                Write-Error "   Error: $($stage_obj.error_message)"
            }
        }
        Write-Host ""
        Write-Host "   Stages Completed: $($summary.stages_completed), Failed: $($summary.stages_failed)"
        Write-Host ""
        
        return $true
    }
    catch {
        Write-Error "Request failed: $($_.Exception.Message)"
        return $false
    }
}

function Show-Menu {
    Write-Host ""
    Write-Host "Select a demo scenario:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  1. Basic Topology (3 routers, 1 switch)"
    Write-Host "  2. Medium Topology (5 routers, 3 switches, with seed)"
    Write-Host "  3. Large Topology (8 routers, 4 switches)"
    Write-Host "  4. Fast Demo (skip analysis)"
    Write-Host "  5. All Demos (sequential)"
    Write-Host "  6. Open API Documentation"
    Write-Host "  0. Exit"
    Write-Host ""
    
    $choice = Read-Host "Enter choice (0-6)"
    return $choice
}

function Main {
    Write-Host ""
    Write-Host ("=" * 80) -ForegroundColor Green
    Write-Host "  🚀 PIPELINE ORCHESTRATION ENDPOINT - INTERACTIVE DEMO" -ForegroundColor Green
    Write-Host ("=" * 80) -ForegroundColor Green
    Write-Host ""
    
    # Check API
    if (-not (Check-ApiRunning)) {
        exit 1
    }
    
    Write-Host ""
    
    if ($DemoType -ne "interactive") {
        # Run specific demo
        if ($DemoPayloads.ContainsKey($DemoType)) {
            Run-Pipeline -Payload $DemoPayloads[$DemoType] -DemoName $DemoType
        }
        else {
            Write-Error "Unknown demo type: $DemoType"
            Write-Host "Available: $($DemoPayloads.Keys -join ', ')"
        }
    }
    else {
        # Interactive mode
        while ($true) {
            $choice = Show-Menu
            
            switch ($choice) {
                "0" {
                    Write-Host "Goodbye! 👋"
                    break
                }
                "1" {
                    Run-Pipeline -Payload $DemoPayloads["basic"] -DemoName "basic"
                }
                "2" {
                    Run-Pipeline -Payload $DemoPayloads["medium"] -DemoName "medium"
                }
                "3" {
                    Run-Pipeline -Payload $DemoPayloads["large"] -DemoName "large"
                }
                "4" {
                    Run-Pipeline -Payload $DemoPayloads["fast"] -DemoName "fast"
                }
                "5" {
                    foreach ($key in $DemoPayloads.Keys) {
                        Run-Pipeline -Payload $DemoPayloads[$key] -DemoName $key
                    }
                }
                "6" {
                    Write-Info "Opening API documentation in browser..."
                    Start-Process "http://localhost:8000/docs"
                }
                default {
                    Write-Warning "Invalid choice"
                }
            }
            
            if ($choice -eq "0") { break }
        }
    }
    
    Write-Host ""
    Write-Host ("=" * 80) -ForegroundColor Cyan
    Write-Host "📚 Documentation: PIPELINE_ORCHESTRATION.md" -ForegroundColor Cyan
    Write-Host "📖 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ("=" * 80) -ForegroundColor Cyan
    Write-Host ""
}

# Run main
Main
