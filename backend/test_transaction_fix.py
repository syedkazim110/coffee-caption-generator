#!/usr/bin/env python3
"""
Test script to verify transaction error fixes
"""

import sys
from brand_manager import BrandManager
from llm_rag_caption_generator import LLMRAGCaptionGenerator
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_brand_manager():
    """Test BrandManager's get_active_brand with error handling"""
    print("\n" + "=" * 60)
    print("Testing BrandManager.get_active_brand()")
    print("=" * 60)
    
    try:
        manager = BrandManager()
        logger.info("BrandManager initialized successfully")
        
        # Test getting active brand (this is where the error was occurring)
        active_brand = manager.get_active_brand()
        
        if active_brand:
            logger.info(f"✅ Successfully retrieved active brand: {active_brand['brand_name']}")
            logger.info(f"   Brand ID: {active_brand['id']}")
            logger.info(f"   Brand Type: {active_brand['brand_type']}")
            return True
        else:
            logger.warning("⚠️  No active brand found (this is OK if database is empty)")
            return True
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False
    finally:
        if 'manager' in locals():
            manager.close()

def test_caption_generator():
    """Test LLMRAGCaptionGenerator's load_brand_profile with error handling"""
    print("\n" + "=" * 60)
    print("Testing LLMRAGCaptionGenerator.load_brand_profile()")
    print("=" * 60)
    
    try:
        generator = LLMRAGCaptionGenerator()
        logger.info("LLMRAGCaptionGenerator initialized successfully")
        
        # Test loading brand profile (this is where the error was occurring)
        generator.load_brand_profile()
        
        if generator.brand_profile:
            logger.info(f"✅ Successfully loaded brand profile: {generator.brand_name}")
            logger.info(f"   Voice adjectives: {', '.join(generator.brand_voice_adjectives[:3])}")
            logger.info(f"   Image style: {generator.brand_image_style[:50]}...")
            return True
        else:
            logger.warning("⚠️  Using default brand settings (this is OK)")
            return True
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 TRANSACTION ERROR FIX - TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Test 1: BrandManager
    results.append(("BrandManager.get_active_brand()", test_brand_manager()))
    
    # Test 2: Caption Generator
    results.append(("LLMRAGCaptionGenerator.load_brand_profile()", test_caption_generator()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Transaction errors should be fixed!")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME TESTS FAILED - Please review the errors above")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
