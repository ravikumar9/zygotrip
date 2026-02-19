"""Enterprise Validator - Main Loop Executor"""

import subprocess
import sys
import os
from repair_engine import run_repairs

def main():
    """Main validation and repair loop"""
    
    os.chdir(os.path.dirname(__file__))
    
    max_iterations = 10
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n{'='*60}")
        print(f"ITERATION {iteration}/{max_iterations}")
        print(f"{'='*60}")
        
        # Run validator
        print("\n🔍 Running validator...")
        result = subprocess.run([sys.executable, "runner.py"], capture_output=False)
        
        if result.returncode == 0:
            print("\n" + "="*60)
            print("✅ ALL VALIDATIONS PASSED")
            print("="*60)
            return 0
        
        # Check if repairs are available
        print("\n🔧 Attempting repairs...")
        if not run_repairs():
            print("❌ No repairs available - stopping")
            return 1
        
        print("✓ Repairs applied - retesting...")
    
    print("\n❌ Max iterations reached without success")
    return 1

if __name__ == "__main__":
    exit_code = main()
    
    if exit_code == 0:
        print("\n" + "="*60)
        print("SYSTEM_FIXED")
        print("="*60)
    
    sys.exit(exit_code)
