"""
Test script for API endpoints.
Run this to verify the system is working correctly.
"""
import requests
import json
from typing import Dict, Any

API_URL = "http://localhost:8000"


def print_section(title: str):
    """Print a section header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")


def test_health_check() -> bool:
    """Test health check endpoint."""
    print_section("Testing Health Check")
    
    try:
        response = requests.get(f"{API_URL}/")
        data = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print("❌ Health check failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_schema_endpoint() -> bool:
    """Test schema endpoint."""
    print_section("Testing Schema Endpoint")
    
    try:
        response = requests.get(f"{API_URL}/schema")
        data = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Table: {data.get('table_name')}")
        print(f"Columns: {len(data.get('columns', []))}")
        print(f"\nFirst 5 columns: {data.get('columns', [])[:5]}")
        
        if response.status_code == 200:
            print("✅ Schema endpoint passed")
            return True
        else:
            print("❌ Schema endpoint failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_sample_data() -> bool:
    """Test sample data endpoint."""
    print_section("Testing Sample Data Endpoint")
    
    try:
        response = requests.get(f"{API_URL}/sample-data?limit=3")
        data = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Rows returned: {data.get('row_count')}")
        print(f"Columns: {data.get('columns')}")
        print(f"\nFirst row: {json.dumps(data.get('data', [])[0], indent=2)}")
        
        if response.status_code == 200:
            print("✅ Sample data endpoint passed")
            return True
        else:
            print("❌ Sample data endpoint failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_query(query: str, test_name: str) -> bool:
    """Test a query."""
    print_section(f"Testing Query: {test_name}")
    
    print(f"Query: {query}")
    
    try:
        response = requests.post(
            f"{API_URL}/query",
            json={"query": query}
        )
        data = response.json()
        
        print(f"\nStatus: {response.status_code}")
        print(f"Detected Intent: {data.get('detected_intent')}")
        print(f"Queries Executed: {len(data.get('query_results', []))}")
        print(f"Errors: {len(data.get('errors', []))}")
        
        print(f"\nResponse:")
        print(data.get('response'))
        
        if data.get('chart_config'):
            print("\n📊 Visualization generated")
        
        if data.get('query_results'):
            print(f"\nSQL Queries:")
            for i, qr in enumerate(data['query_results'], 1):
                print(f"  {i}. {qr.get('sql_query')}")
        
        if data.get('errors'):
            print(f"\n⚠️ Errors:")
            for error in data['errors']:
                print(f"  - {error}")
            print("❌ Query had errors")
            return False
        
        if response.status_code == 200 and data.get('response'):
            print("✅ Query passed")
            return True
        else:
            print("❌ Query failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("\n" + "🧪 Starting API Tests".center(60, "="))
    
    results = []
    
    # Health check
    results.append(("Health Check", test_health_check()))
    
    # Schema
    results.append(("Schema Endpoint", test_schema_endpoint()))
    
    # Sample data
    results.append(("Sample Data", test_sample_data()))
    
    # Simple lookup
    results.append((
        "Simple Lookup",
        test_query("What is Apple's market cap?", "Simple Lookup")
    ))
    
    # Comparison
    results.append((
        "Comparison",
        test_query(
            "Compare revenue of Apple and Microsoft",
            "Company Comparison"
        )
    ))
    
    # Ranking
    results.append((
        "Ranking",
        test_query("Top 5 companies by revenue", "Top N Ranking")
    ))
    
    # Aggregation
    results.append((
        "Aggregation",
        test_query(
            "What's the average PE ratio in the technology sector?",
            "Sector Aggregation"
        )
    ))
    
    # Filter
    results.append((
        "Filter",
        test_query(
            "Companies with market cap over 1 trillion",
            "Filtered Query"
        )
    ))
    
    # Visualization
    results.append((
        "Visualization",
        test_query(
            "Show me a chart of top 10 companies by market cap",
            "Chart Request"
        )
    ))
    
    # Summary
    print_section("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%\n")
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print("\n" + "="*60 + "\n")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️ Some tests failed. Check logs above.")
    
    return passed == total


if __name__ == "__main__":
    import sys
    
    print("S&P 500 Multi-Agent Chatbot - API Test Suite")
    print("Make sure the API server is running on http://localhost:8000")
    input("Press Enter to continue...")
    
    success = run_all_tests()
    
    sys.exit(0 if success else 1)