#!/usr/bin/env python
"""
Simple test script to verify deployment readiness
"""
import os
import sys

def test_requirements():
    """Test if all required packages can be imported"""
    print("🧪 Testing package imports...")
    
    required_packages = [
        'streamlit',
        'agno',
        'chromadb', 
        'pypdf',
        'docx',
        'sentence_transformers',
        'dotenv',
        'google.generativeai'
    ]
    
    failed_imports = []
    
    for package in required_packages:
        try:
            if package == 'docx':
                __import__('docx')
            elif package == 'google.generativeai':
                __import__('google.generativeai')
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError as e:
            print(f"❌ {package}: {e}")
            failed_imports.append(package)
    
    return len(failed_imports) == 0

def test_api_keys():
    """Test if API keys are available"""
    print("\n🔑 Testing API keys...")
    
    google_key = os.getenv("GOOGLE_API_KEY")
    hf_token = os.getenv("HF_TOKEN")
    
    if google_key:
        print("✅ GOOGLE_API_KEY found")
    else:
        print("❌ GOOGLE_API_KEY missing")
    
    if hf_token:
        print("✅ HF_TOKEN found")
    else:
        print("⚠️ HF_TOKEN missing (optional)")
    
    return bool(google_key)

def test_data_files():
    """Test if data files exist"""
    print("\n📁 Testing data files...")
    
    data_dir = "data"
    if not os.path.exists(data_dir):
        print(f"❌ Data directory '{data_dir}' not found")
        return False
    
    files = [f for f in os.listdir(data_dir) if f.endswith(('.pdf', '.docx'))]
    
    if files:
        print(f"✅ Found {len(files)} document(s):")
        for f in files[:5]:  # Show first 5
            print(f"   📄 {f}")
        if len(files) > 5:
            print(f"   ... and {len(files) - 5} more")
    else:
        print("❌ No PDF or DOCX files found in data directory")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Deployment Readiness Test\n")
    
    tests = [
        ("Package Imports", test_requirements),
        ("API Keys", test_api_keys),
        ("Data Files", test_data_files)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test error: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for deployment!")
        return True
    else:
        print("⚠️ Some tests failed. Fix issues before deploying.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
