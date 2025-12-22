#!/usr/bin/env python3
"""
Security test to verify JWT authentication is working properly.
This script tests that all sensitive endpoints require authentication.
"""

import asyncio
import httpx
import os
from typing import Dict, Any

class SecurityTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
        
    async def test_endpoint_protection(self, endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test if an endpoint properly rejects unauthenticated requests."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = await self.client.get(url)
            elif method == "POST":
                response = await self.client.post(url, json=data)
            elif method == "PUT":
                response = await self.client.put(url, json=data)
            elif method == "DELETE":
                response = await self.client.delete(url)
            else:
                return {"error": f"Unsupported method: {method}"}
                
            return {
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "is_protected": response.status_code == 401,
                "requires_auth": True,
                "test_passed": response.status_code == 401
            }
        except Exception as e:
            return {
                "endpoint": endpoint,
                "method": method,
                "error": str(e),
                "test_passed": False
            }

    async def run_security_tests(self) -> Dict[str, Any]:
        """Run comprehensive security tests on all API endpoints."""
        
        # List of sensitive endpoints that should require authentication
        endpoints_to_test = [
            # Notes endpoints
            ("/api/v1/notes", "GET"),
            ("/api/v1/notes", "POST", {"content": "test", "note_type": "permanent"}),
            ("/api/v1/notes/00000000-0000-0000-0000-000000000000", "GET"),
            ("/api/v1/notes/00000000-0000-0000-0000-000000000000", "PUT", {"content": "updated"}),
            ("/api/v1/notes/00000000-0000-0000-0000-000000000000", "DELETE"),
            
            # Search endpoints
            ("/api/v1/search", "POST", {"query": "test"}),
            ("/api/v1/search/stats", "GET"),
            ("/api/v1/search/health", "GET"),
            ("/api/v1/search/similar/00000000-0000-0000-0000-000000000000", "GET"),
            
            # Agent endpoints
            ("/api/v1/agent/runs", "POST", {"agent_type": "researcher"}),
            ("/api/v1/agent/runs/00000000-0000-0000-0000-000000000000", "GET"),
            
            # Ingestion endpoints
            ("/api/v1/ingestion/pdf", "POST"),
            ("/api/v1/ingestion/pdf/00000000-0000-0000-0000-000000000000", "GET"),
            
            # Other sensitive endpoints
            ("/api/v1/research/workflows", "GET"),
            ("/api/v1/quality/reviews", "GET"),
            ("/api/v1/vault/sync", "POST"),
            ("/api/v1/obsidian/notes", "GET"),
        ]
        
        # Public endpoints that should NOT require authentication
        public_endpoints = [
            ("/health", "GET"),
            ("/", "GET"),
            ("/api/v1/system/status", "GET"),
            ("/api/v1/system/readiness", "GET"),
            ("/api/v1/system/liveness", "GET"),
        ]
        
        print("🔐 Testing Security: Authentication Protection")
        print("=" * 50)
        
        # Test sensitive endpoints
        sensitive_results = []
        for endpoint_info in endpoints_to_test:
            endpoint = endpoint_info[0]
            method = endpoint_info[1]
            data = endpoint_info[2] if len(endpoint_info) > 2 else None
            
            result = await self.test_endpoint_protection(endpoint, method, data)
            sensitive_results.append(result)
            
            status = "✅ PROTECTED" if result.get("test_passed") else "❌ VULNERABLE"
            print(f"{status} {method} {endpoint}")
        
        # Test public endpoints
        print("\n🌍 Testing Public Endpoints (should be accessible):")
        print("=" * 50)
        
        public_results = []
        for endpoint_info in public_endpoints:
            endpoint = endpoint_info[0]
            method = endpoint_info[1]
            
            result = await self.test_endpoint_protection(endpoint, method)
            # Public endpoints should NOT return 401
            is_public_ok = not result.get("is_protected", True)
            result["test_passed"] = is_public_ok
            
            status = "✅ PUBLIC" if is_public_ok else "❌ OVER-PROTECTED"
            print(f"{status} {method} {endpoint}")
        
        # Calculate results
        total_sensitive = len(sensitive_results)
        protected_sensitive = sum(1 for r in sensitive_results if r.get("test_passed"))
        
        total_public = len(public_results)
        correct_public = sum(1 for r in public_results if r.get("test_passed"))
        
        # Overall security score
        security_score = (protected_sensitive + correct_public) / (total_sensitive + total_public) * 100
        
        print("\n📊 Security Assessment Results:")
        print("=" * 50)
        print(f"Sensitive Endpoints Protected: {protected_sensitive}/{total_sensitive}")
        print(f"Public Endpoints Correctly Open: {correct_public}/{total_public}")
        print(f"Overall Security Score: {security_score:.1f}%")
        
        if security_score >= 90:
            print("🎉 EXCELLENT: Authentication is properly implemented!")
        elif security_score >= 80:
            print("⚠️  GOOD: Mostly protected, but some issues found.")
        else:
            print("🚨 VULNERABLE: Significant security issues found!")
            
        return {
            "security_score": security_score,
            "sensitive_results": sensitive_results,
            "public_results": public_results,
            "assessment": "SECURE" if security_score >= 90 else "NEEDS_ATTENTION"
        }

async def main():
    """Run security tests."""
    # Set up base URL
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    print(f"🧪 Running security tests on {base_url}")
    print()
    
    tester = SecurityTester(base_url)
    results = await tester.run_security_tests()
    
    # Return appropriate exit code
    exit_code = 0 if results["assessment"] == "SECURE" else 1
    exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())