#!/usr/bin/env python3
"""
Test script for AI-powered Multilingual Telemedicine Platform
Tests all major functionalities including API integrations and translations.
"""

import os
import sys
import json
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all required imports"""
    print("🔍 Testing imports...")

    try:
        from services.ai_engine import (
            detect_urgency, analyze_symptoms, verify_medicine,
            translate_text, get_supported_languages, query_groq_medical_info
        )
        from services.prescription_service import create_prescription, get_prescription
        from services.auth_service import register_user, update_patient_language
        from config import Config
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_ai_engine():
    """Test AI engine functionality"""
    print("\n🤖 Testing AI Engine...")

    try:
        from services.ai_engine import detect_urgency, analyze_symptoms, verify_medicine, translate_text

        # Test urgency detection
        urgency = detect_urgency("I have chest pain and difficulty breathing")
        print(f"Urgency detection: {urgency['severity']} - {urgency['alert_message']}")

        # Test symptom analysis
        analysis = analyze_symptoms("I have fever, cough, and body ache for 3 days")
        print(f"Symptom analysis: {analysis['diagnosis']} (confidence: {analysis['confidence']})")

        # Test medicine verification
        medicine = verify_medicine("paracetamol")
        print(f"Medicine verification: {medicine['name']} - {medicine['category']}")

        # Test translation
        translated = translate_text("Take medicine after food", 'en', 'hi')
        print(f"Translation: {translated}")

        print("✅ AI Engine tests completed")
        return True
    except Exception as e:
        print(f"❌ AI Engine test failed: {e}")
        return False

def test_prescription_service():
    """Test prescription service"""
    print("\n💊 Testing Prescription Service...")

    try:
        # This would require database setup, so we'll just test the functions exist
        from services.prescription_service import create_prescription, get_prescription

        print("✅ Prescription service functions available")
        return True
    except Exception as e:
        print(f"❌ Prescription service test failed: {e}")
        return False

def test_api_availability():
    """Test external API availability"""
    print("\n🌐 Testing External APIs...")

    try:
        from config import Config

        apis_status = {
            "Groq API": bool(Config.GROQ_API_KEY),
            "Gemini API": bool(Config.GEMINI_API_KEY)
        }

        for api, available in apis_status.items():
            status = "✅ Available" if available else "⚠️ Not configured"
            print(f"{api}: {status}")

        # Test Groq if available
        if Config.GROQ_API_KEY:
            from services.ai_engine import query_groq_medical_info
            try:
                result = query_groq_medical_info("What are symptoms of common cold?", timeout=10)
                if result:
                    print("✅ Groq API responding")
                else:
                    print("⚠️ Groq API not responding")
            except:
                print("❌ Groq API error")

        print("✅ API availability test completed")
        return True
    except Exception as e:
        print(f"❌ API availability test failed: {e}")
        return False

def test_database_schema():
    """Test database schema"""
    print("\n🗄️ Testing Database Schema...")

    try:
        from database import init_db
        init_db()
        print("✅ Database schema initialized")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 AI-Powered Multilingual Telemedicine Platform - Test Suite")
    print("=" * 60)

    start_time = datetime.now()

    # Run tests
    tests = [
        test_imports,
        test_ai_engine,
        test_prescription_service,
        test_api_availability,
        test_database_schema
    ]

    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed: {e}")

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{len(tests)} tests passed")
    print(".2f")
    print("🎉 Testing completed!")

    if passed == len(tests):
        print("✅ All systems operational!")
        return 0
    else:
        print("⚠️ Some tests failed. Check configuration and dependencies.")
        return 1

if __name__ == "__main__":
    sys.exit(main())