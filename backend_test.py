#!/usr/bin/env python3
"""
Comprehensive Backend Test Suite for AI Time Machine
Tests LLM integration, Wikipedia API, Timeline generation, and Database operations
"""

import requests
import json
import time
import sys
from typing import Dict, List, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from frontend environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE_URL = f"{BACKEND_URL}/api"

class AITimeMachineBackendTester:
    def __init__(self):
        self.api_base = API_BASE_URL
        self.test_results = {
            'api_connectivity': False,
            'wikipedia_integration': False,
            'llm_integration': False,
            'timeline_generation': False,
            'database_operations': False,
            'error_handling': False
        }
        self.generated_timeline_id = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_api_connectivity(self) -> bool:
        """Test basic API connectivity"""
        self.log("Testing API connectivity...")
        try:
            response = requests.get(f"{self.api_base}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('message') == 'AI Time Machine API':
                    self.log("✅ API connectivity test passed")
                    return True
                else:
                    self.log(f"❌ Unexpected API response: {data}", "ERROR")
                    return False
            else:
                self.log(f"❌ API returned status code: {response.status_code}", "ERROR")
                return False
        except requests.exceptions.RequestException as e:
            self.log(f"❌ API connectivity failed: {e}", "ERROR")
            return False
    
    def test_wikipedia_integration(self) -> bool:
        """Test Wikipedia API integration by checking if historical context extraction works"""
        self.log("Testing Wikipedia API integration...")
        try:
            # Test scenario that should trigger Wikipedia searches
            test_scenario = "What if Gandhi had access to modern communication technology during the Indian independence movement?"
            
            # We'll test this indirectly through the timeline generation endpoint
            # since Wikipedia integration is internal to the backend
            payload = {
                "scenario": test_scenario,
                "depth": "brief"
            }
            
            response = requests.post(
                f"{self.api_base}/generate-timeline",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                # Check if historical context was extracted
                if 'historical_context' in data and len(data['historical_context']) > 0:
                    self.log("✅ Wikipedia integration test passed - historical context extracted")
                    self.generated_timeline_id = data.get('id')
                    return True
                else:
                    self.log("❌ Wikipedia integration failed - no historical context found", "ERROR")
                    return False
            else:
                self.log(f"❌ Wikipedia integration test failed with status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Wikipedia integration test failed: {e}", "ERROR")
            return False
    
    def test_llm_integration(self) -> bool:
        """Test Gemini-2.5-Pro LLM integration"""
        self.log("Testing LLM integration with Gemini-2.5-Pro...")
        try:
            # Test with a simple scenario that should generate a clear timeline
            test_scenario = "What if the printing press was invented 100 years earlier in medieval Europe?"
            
            payload = {
                "scenario": test_scenario,
                "depth": "brief"
            }
            
            response = requests.post(
                f"{self.api_base}/generate-timeline",
                json=payload,
                timeout=45  # LLM calls can take longer
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate LLM-generated content
                required_fields = ['summary', 'timeline_events', 'original_scenario']
                for field in required_fields:
                    if field not in data:
                        self.log(f"❌ LLM integration failed - missing field: {field}", "ERROR")
                        return False
                
                # Check timeline events structure
                if len(data['timeline_events']) > 0:
                    event = data['timeline_events'][0]
                    event_fields = ['year', 'date', 'event', 'impact', 'probability']
                    for field in event_fields:
                        if field not in event:
                            self.log(f"❌ LLM integration failed - missing event field: {field}", "ERROR")
                            return False
                    
                    self.log("✅ LLM integration test passed - timeline generated successfully")
                    if not self.generated_timeline_id:
                        self.generated_timeline_id = data.get('id')
                    return True
                else:
                    self.log("❌ LLM integration failed - no timeline events generated", "ERROR")
                    return False
            else:
                self.log(f"❌ LLM integration test failed with status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ LLM integration test failed: {e}", "ERROR")
            return False
    
    def test_timeline_generation_detailed(self) -> bool:
        """Test detailed timeline generation"""
        self.log("Testing detailed timeline generation...")
        try:
            test_scenario = "What if Albert Einstein had collaborated with Nikola Tesla on wireless energy transmission?"
            
            payload = {
                "scenario": test_scenario,
                "depth": "detailed"
            }
            
            response = requests.post(
                f"{self.api_base}/generate-timeline",
                json=payload,
                timeout=60  # Detailed timelines take longer
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Detailed timelines should have more events
                if len(data.get('timeline_events', [])) >= 5:
                    self.log("✅ Detailed timeline generation test passed")
                    return True
                else:
                    self.log(f"❌ Detailed timeline has insufficient events: {len(data.get('timeline_events', []))}", "ERROR")
                    return False
            else:
                self.log(f"❌ Detailed timeline generation failed with status: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Detailed timeline generation test failed: {e}", "ERROR")
            return False
    
    def test_database_operations(self) -> bool:
        """Test MongoDB database operations"""
        self.log("Testing database operations...")
        try:
            # Test retrieving all timelines
            response = requests.get(f"{self.api_base}/timelines", timeout=10)
            if response.status_code != 200:
                self.log(f"❌ Failed to retrieve timelines: {response.status_code}", "ERROR")
                return False
            
            timelines = response.json()
            if not isinstance(timelines, list):
                self.log("❌ Timelines endpoint did not return a list", "ERROR")
                return False
            
            self.log(f"Retrieved {len(timelines)} timelines from database")
            
            # Test retrieving specific timeline if we have one
            if self.generated_timeline_id and len(timelines) > 0:
                # Find a timeline ID from the list
                timeline_id = timelines[0].get('id') if timelines else self.generated_timeline_id
                
                response = requests.get(f"{self.api_base}/timeline/{timeline_id}", timeout=10)
                if response.status_code == 200:
                    timeline = response.json()
                    if timeline.get('id') == timeline_id:
                        self.log("✅ Database operations test passed")
                        return True
                    else:
                        self.log("❌ Retrieved timeline ID mismatch", "ERROR")
                        return False
                else:
                    self.log(f"❌ Failed to retrieve specific timeline: {response.status_code}", "ERROR")
                    return False
            else:
                self.log("✅ Database operations test passed (basic retrieval)")
                return True
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Database operations test failed: {e}", "ERROR")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling for invalid inputs"""
        self.log("Testing error handling...")
        try:
            # Test with empty scenario
            payload = {"scenario": "", "depth": "brief"}
            response = requests.post(f"{self.api_base}/generate-timeline", json=payload, timeout=10)
            
            # Should handle gracefully (either 400 or generate something)
            if response.status_code in [200, 400, 422]:
                self.log("✅ Empty scenario handled appropriately")
            else:
                self.log(f"❌ Unexpected status for empty scenario: {response.status_code}", "ERROR")
                return False
            
            # Test invalid timeline ID
            response = requests.get(f"{self.api_base}/timeline/invalid-id-12345", timeout=10)
            if response.status_code == 404:
                self.log("✅ Invalid timeline ID handled correctly (404)")
            else:
                self.log(f"❌ Invalid timeline ID not handled correctly: {response.status_code}", "ERROR")
                return False
            
            # Test invalid depth parameter
            payload = {"scenario": "Test scenario", "depth": "invalid_depth"}
            response = requests.post(f"{self.api_base}/generate-timeline", json=payload, timeout=10)
            
            # Should either accept it or return validation error
            if response.status_code in [200, 400, 422]:
                self.log("✅ Invalid depth parameter handled appropriately")
                return True
            else:
                self.log(f"❌ Unexpected status for invalid depth: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Error handling test failed: {e}", "ERROR")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all backend tests"""
        self.log("=" * 60)
        self.log("Starting AI Time Machine Backend Test Suite")
        self.log(f"Testing against: {self.api_base}")
        self.log("=" * 60)
        
        # Test 1: API Connectivity
        self.test_results['api_connectivity'] = self.test_api_connectivity()
        
        # Test 2: Wikipedia Integration (via timeline generation)
        if self.test_results['api_connectivity']:
            self.test_results['wikipedia_integration'] = self.test_wikipedia_integration()
        
        # Test 3: LLM Integration
        if self.test_results['api_connectivity']:
            self.test_results['llm_integration'] = self.test_llm_integration()
        
        # Test 4: Timeline Generation (detailed)
        if self.test_results['llm_integration']:
            self.test_results['timeline_generation'] = self.test_timeline_generation_detailed()
        
        # Test 5: Database Operations
        if self.test_results['api_connectivity']:
            self.test_results['database_operations'] = self.test_database_operations()
        
        # Test 6: Error Handling
        if self.test_results['api_connectivity']:
            self.test_results['error_handling'] = self.test_error_handling()
        
        return self.test_results
    
    def print_summary(self):
        """Print test results summary"""
        self.log("=" * 60)
        self.log("TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.replace('_', ' ').title()}: {status}")
        
        self.log("=" * 60)
        self.log(f"OVERALL: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL TESTS PASSED! Backend is working correctly.")
        else:
            self.log("⚠️  Some tests failed. Check the logs above for details.")
        
        return passed_tests == total_tests

def main():
    """Main test execution"""
    tester = AITimeMachineBackendTester()
    results = tester.run_all_tests()
    success = tester.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()