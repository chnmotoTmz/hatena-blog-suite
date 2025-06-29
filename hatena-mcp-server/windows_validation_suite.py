#!/usr/bin/env python3
"""Windows Validation Suite - Comprehensive Testing for Hatena Multi-Blog System"""

import os
import sys
import json
import time
from typing import Dict, List, Optional
import platform

# Add Windows-specific encoding support
if platform.system() == "Windows":
    sys.stdout.reconfigure(encoding='utf-8')

def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def print_test_result(test_name: str, success: bool, message: str = ""):
    """Print formatted test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if message:
        print(f"    {message}")

class WindowsValidationSuite:
    """Comprehensive validation suite for Windows deployment"""
    
    def __init__(self):
        self.results = {
            "environment": {},
            "dependencies": {},
            "configuration": {},
            "authentication": {},
            "functionality": {},
            "performance": {}
        }
    
    def test_environment(self) -> bool:
        """Test 1: Environment validation"""
        print_section("Environment Validation")
        
        all_passed = True
        
        # Python version check
        python_version = sys.version_info
        version_ok = python_version >= (3, 9)
        print_test_result("Python Version", version_ok, 
                         f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        self.results["environment"]["python_version"] = f"{python_version.major}.{python_version.minor}.{python_version.micro}"
        all_passed &= version_ok
        
        # Platform check
        platform_info = platform.system()
        print_test_result("Platform", True, platform_info)
        self.results["environment"]["platform"] = platform_info
        
        # Working directory check
        cwd = os.getcwd()
        print_test_result("Working Directory", True, cwd)
        self.results["environment"]["working_directory"] = cwd
        
        return all_passed
    
    def test_dependencies(self) -> bool:
        """Test 2: Dependencies validation"""
        print_section("Dependencies Validation")
        
        all_passed = True
        required_packages = ["requests", "dotenv"]
        
        for package in required_packages:
            try:
                if package == "dotenv":
                    from dotenv import load_dotenv
                    module_name = "python-dotenv"
                else:
                    __import__(package)
                    module_name = package
                
                print_test_result(f"Package: {module_name}", True, "Available")
                self.results["dependencies"][package] = "available"
            except ImportError:
                print_test_result(f"Package: {package}", False, "Missing - run: pip install " + ("python-dotenv" if package == "dotenv" else package))
                self.results["dependencies"][package] = "missing"
                all_passed = False
        
        return all_passed
    
    def test_configuration(self) -> bool:
        """Test 3: Configuration validation"""
        print_section("Configuration Validation")
        
        all_passed = True
        
        # Check for .env file
        env_exists = os.path.exists('.env')
        print_test_result(".env File", env_exists, 
                         "Found" if env_exists else "Missing - copy from .env.template")
        self.results["configuration"]["env_file"] = env_exists
        all_passed &= env_exists
        
        if env_exists:
            try:
                from dotenv import load_dotenv
                load_dotenv()
                
                # Check API keys
                api_key_1 = os.getenv('HATENA_BLOG_ATOMPUB_KEY_1')
                api_key_2 = os.getenv('HATENA_BLOG_ATOMPUB_KEY_2')
                
                key1_ok = api_key_1 is not None and len(api_key_1) > 5
                key2_ok = api_key_2 is not None and len(api_key_2) > 5
                
                print_test_result("API Key 1", key1_ok, 
                                 "Configured" if key1_ok else "Missing or invalid")
                print_test_result("API Key 2", key2_ok,
                                 "Configured" if key2_ok else "Missing or invalid")
                
                self.results["configuration"]["api_key_1"] = key1_ok
                self.results["configuration"]["api_key_2"] = key2_ok
                all_passed &= (key1_ok or key2_ok)  # At least one key needed
                
            except Exception as e:
                print_test_result("Environment Loading", False, str(e))
                all_passed = False
        
        return all_passed
    
    def test_core_imports(self) -> bool:
        """Test 4: Core system imports"""
        print_section("Core System Imports")
        
        all_passed = True
        
        try:
            from multi_blog_manager import MultiBlogManager
            print_test_result("MultiBlogManager", True, "Import successful")
            self.results["functionality"]["multi_blog_manager"] = True
        except ImportError as e:
            print_test_result("MultiBlogManager", False, f"Import failed: {e}")
            self.results["functionality"]["multi_blog_manager"] = False
            all_passed = False
        
        try:
            from enhanced_hatena_agent import EnhancedHatenaAgent
            print_test_result("EnhancedHatenaAgent", True, "Import successful")
            self.results["functionality"]["enhanced_hatena_agent"] = True
        except ImportError as e:
            print_test_result("EnhancedHatenaAgent", False, f"Import failed: {e}")
            self.results["functionality"]["enhanced_hatena_agent"] = False
            all_passed = False
        
        return all_passed
    
    def test_authentication(self) -> bool:
        """Test 5: Authentication validation"""
        print_section("Authentication Testing")
        
        all_passed = True
        
        try:
            from enhanced_hatena_agent import EnhancedHatenaAgent
            agent = EnhancedHatenaAgent()
            
            # Test blog listing
            blogs_result = agent.list_blogs()
            blogs_ok = blogs_result.get("status") == "success"
            blog_count = blogs_result.get("count", 0)
            
            print_test_result("Blog Configuration", blogs_ok,
                             f"Found {blog_count} configured blogs" if blogs_ok else "Configuration error")
            self.results["authentication"]["blog_config"] = blogs_ok
            all_passed &= blogs_ok
            
            if blogs_ok and blog_count > 0:
                # Test authentication for first blog
                auth_result = agent.test_blog_authentication()
                if auth_result.get("status") == "success":
                    success_count = sum(1 for result in auth_result["results"].values() 
                                      if result.get("status") == "success")
                    auth_ok = success_count > 0
                    print_test_result("Authentication Test", auth_ok,
                                     f"{success_count}/{blog_count} blogs authenticated successfully")
                    self.results["authentication"]["auth_success"] = success_count
                else:
                    print_test_result("Authentication Test", False, "Test failed")
                    self.results["authentication"]["auth_success"] = 0
                    all_passed = False
            
        except Exception as e:
            print_test_result("Authentication System", False, f"Error: {e}")
            all_passed = False
        
        return all_passed
    
    def test_basic_functionality(self) -> bool:
        """Test 6: Basic functionality"""
        print_section("Basic Functionality Testing")
        
        all_passed = True
        
        try:
            from enhanced_hatena_agent import EnhancedHatenaAgent
            agent = EnhancedHatenaAgent()
            
            # Test article retrieval (with error handling)
            try:
                articles_result = agent.get_articles('lifehack_blog', limit=3)
                articles_ok = articles_result.get("status") == "success"
                article_count = len(articles_result.get("articles", []))
                
                print_test_result("Article Retrieval", articles_ok,
                                 f"Retrieved {article_count} articles" if articles_ok else "Retrieval failed")
                self.results["functionality"]["article_retrieval"] = articles_ok
            except Exception as e:
                print_test_result("Article Retrieval", False, f"Error: {e}")
                self.results["functionality"]["article_retrieval"] = False
                all_passed = False
            
            # Test search functionality
            try:
                search_result = agent.search_articles_by_title('lifehack_blog', 'test')
                search_ok = search_result.get("status") == "success"
                
                print_test_result("Search Functionality", search_ok,
                                 "Search system operational" if search_ok else "Search failed")
                self.results["functionality"]["search"] = search_ok
            except Exception as e:
                print_test_result("Search Functionality", False, f"Error: {e}")
                self.results["functionality"]["search"] = False
                all_passed = False
            
        except Exception as e:
            print_test_result("Functionality Test", False, f"System error: {e}")
            all_passed = False
        
        return all_passed
    
    def test_performance(self) -> bool:
        """Test 7: Performance benchmarks"""
        print_section("Performance Testing")
        
        all_passed = True
        
        try:
            from enhanced_hatena_agent import EnhancedHatenaAgent
            
            # Import timing
            start_time = time.time()
            agent = EnhancedHatenaAgent()
            import_time = time.time() - start_time
            
            import_ok = import_time < 5.0  # Should load within 5 seconds
            print_test_result("Import Performance", import_ok,
                             f"Loaded in {import_time:.2f}s")
            self.results["performance"]["import_time"] = import_time
            
            # Blog list timing
            start_time = time.time()
            agent.list_blogs()
            list_time = time.time() - start_time
            
            list_ok = list_time < 2.0  # Should complete within 2 seconds
            print_test_result("Blog List Performance", list_ok,
                             f"Completed in {list_time:.2f}s")
            self.results["performance"]["list_time"] = list_time
            
            all_passed &= import_ok and list_ok
            
        except Exception as e:
            print_test_result("Performance Test", False, f"Error: {e}")
            all_passed = False
        
        return all_passed
    
    def run_all_tests(self) -> Dict:
        """Run complete validation suite"""
        print("🪟 Windows Validation Suite for Hatena Multi-Blog System")
        print("🕒 Starting comprehensive validation...")
        
        test_results = {
            "environment": self.test_environment(),
            "dependencies": self.test_dependencies(),
            "configuration": self.test_configuration(),
            "core_imports": self.test_core_imports(),
            "authentication": self.test_authentication(),
            "functionality": self.test_basic_functionality(),
            "performance": self.test_performance()
        }
        
        # Summary
        print_section("Validation Summary")
        
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        overall_success = passed_tests == total_tests
        
        for test_name, result in test_results.items():
            print_test_result(test_name.replace('_', ' ').title(), result)
        
        print(f"\n🎯 Overall Result: {passed_tests}/{total_tests} tests passed")
        
        if overall_success:
            print("\n🎉 System is ready for production use!")
            print("✅ All validation tests passed")
            print("\n📝 Next steps:")
            print("  1. Start using the system with: python enhanced_hatena_agent.py")
            print("  2. Begin article migration with copy_mode=True")
            print("  3. Monitor system performance")
        else:
            print("\n⚠️  System requires attention")
            print("❌ Some validation tests failed")
            print("\n📝 Recommended actions:")
            print("  1. Review failed tests above")
            print("  2. Fix configuration issues")
            print("  3. Re-run validation: python windows_validation_suite.py")
        
        # Save detailed results
        with open('validation_results.json', 'w', encoding='utf-8') as f:
            json.dump({
                "summary": test_results,
                "details": self.results,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "platform": platform.system(),
                "python_version": sys.version
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 Detailed results saved to: validation_results.json")
        
        return test_results

def main():
    """Main validation entry point"""
    try:
        suite = WindowsValidationSuite()
        results = suite.run_all_tests()
        
        # Exit code based on results
        exit_code = 0 if all(results.values()) else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Validation interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n\n❌ Validation suite error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)

if __name__ == "__main__":
    main()