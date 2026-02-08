#!/usr/bin/env python3
"""
Quick demo script for the pipeline orchestration endpoint.
Run this after starting the FastAPI application: python demo_pipeline.py
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"
DEMO_PAYLOADS = {
    "basic": {
        "topology_name": "demo-basic",
        "num_routers": 3,
        "num_switches": 1,
        "run_analysis": True
    },
    "medium": {
        "topology_name": "demo-medium",
        "num_routers": 5,
        "num_switches": 3,
        "seed": 42,
        "run_analysis": True
    },
    "large": {
        "topology_name": "demo-large",
        "num_routers": 8,
        "num_switches": 4,
        "seed": 123,
        "run_analysis": True
    },
    "fast": {
        "topology_name": "demo-fast",
        "num_routers": 3,
        "num_switches": 1,
        "run_analysis": False
    }
}


def print_separator(title=""):
    """Print a styled separator."""
    width = 80
    if title:
        print(f"\n{'='*width}")
        print(f"  {title}")
        print(f"{'='*width}\n")
    else:
        print(f"\n{'-'*width}\n")


def print_result(result):
    """Pretty print the pipeline result."""
    print(f"✅ Pipeline Execution Successful!\n")
    
    # Header info
    print(f"📋 Execution Details:")
    print(f"   Pipeline ID: {result['pipeline_id']}")
    print(f"   Status: {result['overall_status']}")
    print(f"   Timestamp: {result['execution_timestamp']}")
    print(f"   Total Duration: {result['total_duration_seconds']:.2f}s")
    
    # Summary
    summary = result['summary']
    print(f"\n📊 Generated Topology:")
    print(f"   Name: {summary['topology_name']}")
    print(f"   Total Devices: {summary['total_devices']}")
    print(f"   Total Links: {summary['total_links']}")
    print(f"   Routers: {summary['num_routers']}")
    print(f"   Switches: {summary['num_switches']}")
    print(f"   Containerlab Nodes: {summary['containerlab_nodes']}")
    
    # Analysis results (if available)
    if summary.get('analysis_health_score'):
        print(f"\n🔍 Topology Analysis:")
        health = summary['analysis_health_score']
        # Visual health bar
        bar_length = 30
        filled = int((health / 100) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"   Health Score: [{bar}] {health}/100")
        print(f"   Issues Found: {summary['analysis_issues_found']}")
    
    # Stage breakdown
    print(f"\n⚙️  Pipeline Stages:")
    for stage_name, stage in result['stages'].items():
        status_icon = "✅" if stage['status'] == 'success' else "❌"
        duration = f"{stage['duration_seconds']:.4f}s"
        print(f"   {status_icon} {stage_name:30s} {duration}")
        if stage['error_message']:
            print(f"      Error: {stage['error_message']}")
    
    print(f"\n   Total Stages: {summary['stages_completed']} completed, "
          f"{summary['stages_failed']} failed")


def run_demo(demo_type="basic"):
    """Run a demo request."""
    if demo_type not in DEMO_PAYLOADS:
        print(f"❌ Unknown demo type: {demo_type}")
        print(f"Available: {', '.join(DEMO_PAYLOADS.keys())}")
        return False
    
    payload = DEMO_PAYLOADS[demo_type]
    
    print_separator(f"DEMO: {demo_type.upper()} TOPOLOGY")
    print(f"📤 Request Payload:\n{json.dumps(payload, indent=2)}")
    
    try:
        print("\n⏳ Executing pipeline...")
        start = time.time()
        
        response = requests.post(
            f"{BASE_URL}/run-pipeline",
            json=payload,
            timeout=60
        )
        
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            print_result(result)
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Cannot reach the API")
        print("   Make sure the FastAPI application is running on http://localhost:8000")
        return False
    except requests.exceptions.Timeout:
        print("❌ Timeout: Request took too long")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def main():
    """Main demo runner."""
    print("\n" + "="*80)
    print("🚀 PIPELINE ORCHESTRATION ENDPOINT - INTERACTIVE DEMO")
    print("="*80)
    
    # Check API availability
    try:
        print("\n🔄 Checking API availability...")
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API is running and accessible")
        else:
            print("⚠️  API responded but might not be fully ready")
    except:
        print("❌ API is not responding. Make sure to start it first:")
        print("   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return
    
    print_separator()
    print("Select a demo scenario or enter 'all' to run all demos:\n")
    for i, (key, payload) in enumerate(DEMO_PAYLOADS.items(), 1):
        print(f"  {i}. {key.upper():8s} - {payload['num_routers']} routers, "
              f"{payload['num_switches']} switches "
              f"(Analysis: {'Yes' if payload.get('run_analysis', True) else 'No'})")
    
    print(f"  0. Exit")
    print()
    
    choice = input("Enter choice (0-{}) or demo name: ".format(len(DEMO_PAYLOADS))).strip().lower()
    
    if choice == "exit" or choice == "0":
        print("Goodbye! 👋")
        return
    elif choice == "all":
        for demo_type in DEMO_PAYLOADS.keys():
            run_demo(demo_type)
            print_separator()
    elif choice in DEMO_PAYLOADS:
        run_demo(choice)
    else:
        try:
            index = int(choice) - 1
            if 0 <= index < len(DEMO_PAYLOADS):
                demo_type = list(DEMO_PAYLOADS.keys())[index]
                run_demo(demo_type)
            else:
                print("❌ Invalid choice")
        except ValueError:
            print("❌ Invalid input")
    
    print_separator()
    print("Demo completed! 🎉\n")
    print("📚 For API documentation, visit: http://localhost:8000/docs")
    print("📖 For more details, see: PIPELINE_ORCHESTRATION.md")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo cancelled. Goodbye! 👋")
        sys.exit(0)
