"""Enterprise Validator - Master Runner"""

import importlib
import pkgutil
import json
import time
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def main():
    """Run all validation tests and generate report"""
    
    failures = []
    results = {}
    
    print("\n" + "="*60)
    print("🚀 ENTERPRISE VALIDATOR - STARTING")
    print("="*60)
    
    # Import and run all test modules
    test_modules = ['header', 'layout', 'cards', 'filters', 'booking', 'network', 'console', 'visual']
    
    for modname in test_modules:
        try:
            print(f"\n📋 Running test: {modname}...", end=" ", flush=True)
            module = importlib.import_module(f"tests.{modname}")
            
            start = time.time()
            errs = module.run()
            elapsed_ms = round((time.time() - start) * 1000)
            
            results[modname] = {
                "errors": errs,
                "time": elapsed_ms
            }
            
            if errs:
                status = f"❌ FAIL ({len(errs)} errors)"
                failures.extend([(modname, e) for e in errs])
            else:
                status = "✅ PASS"
            
            print(status)
            if errs:
                for err in errs[:3]:  # Show first 3 errors
                    print(f"   ⚠️  {err}")
                if len(errs) > 3:
                    print(f"   ... and {len(errs)-3} more")
        
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            results[modname] = {
                "errors": [str(e)],
                "time": 0
            }
            failures.append((modname, str(e)))
    
    # Save results
    with open(os.path.join(os.path.dirname(__file__), "results.json"), "w") as f:
        json.dump(results, f, indent=2)
    
    # Generate dashboard
    try:
        from dashboard import generate_dashboard
        generate_dashboard()
        print("\n📊 Dashboard generated: dashboard.html")
    except Exception as e:
        print(f"⚠️  Dashboard generation failed: {str(e)}")
    
    # Print summary
    print("\n" + "="*60)
    total_failures = sum(len(v["errors"]) for v in results.values())
    
    if total_failures == 0:
        print("✅ TOTAL_FAILURES = 0")
        print("="*60 + "\n")
        return 0
    else:
        print(f"❌ TOTAL_FAILURES = {total_failures}")
        print("\nFailed tests:")
        for test_name, error in failures:
            print(f"  • {test_name}: {error}")
        print("="*60 + "\n")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)