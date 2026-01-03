"""
Diagnostic Script - Find Why API is Crashing
Run this to identify the exact issue
"""
import requests
import json
import sys

API_URL = "http://localhost:8000"

def test_step(step_name, func):
    """Run a test step and show results"""
    print(f"\n{'='*60}")
    print(f"TEST: {step_name}")
    print('='*60)
    try:
        result = func()
        print("✅ PASSED")
        return result
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_1_api_running():
    """Test if API server is running"""
    response = requests.get(f"{API_URL}/", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_2_health_check():
    """Test health endpoint"""
    response = requests.get(f"{API_URL}/health", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_3_xgb_service():
    """Test if XGBoost service is reachable"""
    # Try to call XGBoost service directly if running locally
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        print(f"✅ XGBoost service is running")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return True
    except:
        print(f"⚠️ XGBoost service not reachable at localhost:8001")
        print(f"This is OK if using docker/kubernetes")
        return None

def test_4_hw_service():
    """Test if Holt-Winters service is reachable"""
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        print(f"✅ Holt-Winters service is running")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return True
    except:
        print(f"⚠️ Holt-Winters service not reachable at localhost:8002")
        print(f"This is OK if using docker/kubernetes")
        return None

def test_5_forecast_low_carbon():
    """Test forecast with LOW carbon mode"""
    url = f"{API_URL}/forecast/optimized/DE"
    params = {"carbon_mode": "LOW"}
    
    print(f"URL: {url}")
    print(f"Params: {params}")
    
    response = requests.get(url, params=params, timeout=60)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        metadata = data.get("metadata", {})
        forecast = data.get("forecast", [])
        
        print(f"\nMetadata:")
        print(json.dumps(metadata, indent=2))
        
        # ✅ CHECK FOR EMERGENCY FALLBACK
        if metadata.get("selected_model") == "Emergency Static Fallback":
            print(f"\n❌ EMERGENCY FALLBACK ACTIVATED!")
            print(f"Error: {metadata.get('error', 'Unknown')}")
            return False  # ← Changed from True
        
        # ✅ CHECK FOR REAL MODEL
        if "XGBoost" not in metadata.get("selected_model", "") and "Holt-Winters" not in metadata.get("selected_model", ""):
            print(f"\n❌ Unexpected model: {metadata.get('selected_model')}")
            return False
        
        print(f"\n✅ Real forecast from: {metadata.get('selected_model')}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_6_forecast_high_carbon():
    """Test forecast with HIGH carbon mode"""
    url = f"{API_URL}/forecast/optimized/DE"
    params = {"carbon_mode": "HIGH"}
    
    print(f"URL: {url}")
    print(f"Params: {params}")
    
    response = requests.get(url, params=params, timeout=60)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        metadata = data.get("metadata", {})
        print(f"\nMetadata:")
        print(json.dumps(metadata, indent=2))
        return True
    else:
        print(f"Error: {response.text}")
        return False

def main():
    print("╔════════════════════════════════════════════════════════╗")
    print("║   API DIAGNOSTIC TOOL - Find Connection Issues        ║")
    print("╚════════════════════════════════════════════════════════╝")
    
    # Run tests
    results = {}
    results['api_running'] = test_step("1. API Server Running", test_1_api_running)
    
    if not results['api_running']:
        print("\n❌ API is not running!")
        print("\n💡 Start your API first:")
        print("   python src/api/main.py")
        print("   OR")
        print("   uvicorn src.api.main:app --reload --port 8000")
        return
    
    results['health'] = test_step("2. Health Check", test_2_health_check)
    results['xgb'] = test_step("3. XGBoost Service", test_3_xgb_service)
    results['hw'] = test_step("4. Holt-Winters Service", test_4_hw_service)
    
    print("\n" + "="*60)
    print("CRITICAL TEST: Full Forecast Request")
    print("="*60)
    print("This is where the connection is dropping...")
    
    results['forecast_low'] = test_step("5. Forecast (LOW carbon)", test_5_forecast_low_carbon)
    
    if results['forecast_low']:
        results['forecast_high'] = test_step("6. Forecast (HIGH carbon)", test_6_forecast_high_carbon)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for test, result in results.items():
        status = "✅" if result else "❌" if result is False else "⚠️"
        print(f"{status} {test}")
    
    print("\n" + "="*60)
    print("DIAGNOSIS")
    print("="*60)
    
    if not results.get('forecast_low'):
        print("\n🔍 The API crashes when processing forecast requests.")
        print("\n📋 Possible causes:")
        print("   1. Missing model files")
        print("   2. Missing dependencies")
        print("   3. Orchestrator can't connect to microservices")
        print("   4. Error in prediction code")
        print("\n💡 Next steps:")
        print("   1. Check the API terminal for error messages")
        print("   2. Look for import errors or file not found errors")
        print("   3. Verify models exist in models/ directory")
        print("   4. Check if XGBoost/HW services are running")
    else:
        print("\n✅ API is working correctly!")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
