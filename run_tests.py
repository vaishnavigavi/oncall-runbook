#!/usr/bin/env python3
"""
Test runner for OnCall Runbook RAG System
"""
import subprocess
import sys
import os

def run_tests():
    """Run all tests"""
    print("🧪 Running OnCall Runbook RAG System Tests...")
    print("=" * 50)
    
    # Change to API directory
    os.chdir('api')
    
    try:
        # Run pytest
        result = subprocess.run([
            'python', '-m', 'pytest', 
            '../tests/', 
            '-v', 
            '--tb=short'
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        print(f"\n{'='*50}")
        print(f"Tests completed with exit code: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
            
        return result.returncode
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
