#!/usr/bin/env python3
"""
Test script to verify recipe-scrapers backend works with various popular recipe sites
"""
import httpx
import json
from typing import List, Dict, Any

# Test URLs from various popular recipe sites
TEST_URLS = [
    "https://www.allrecipes.com/recipe/158968/spinach-and-feta-turkey-burgers/",
    "https://www.bbcgoodfood.com/recipes/chocolate-chip-cookies",
    "https://www.foodnetwork.com/recipes/alton-brown/chocolate-chip-cookies-recipe-2125436",
    "https://www.seriouseats.com/recipes/2019/04/chocolate-chip-cookies-recipe.html",
    "https://www.bonappetit.com/recipe/chocolate-chip-cookies",
    "https://cooking.nytimes.com/recipes/1024-best-chocolate-chip-cookies",
    "https://www.delish.com/cooking/recipe-ideas/recipes/a58711/best-chocolate-chip-cookies-recipe/",
    "https://www.epicurious.com/recipes/food/views/chocolate-chip-cookies-108703",
    "https://www.simplyrecipes.com/recipes/chocolate_chip_cookies/",
    "https://www.food.com/recipe/best-chocolate-chip-cookies-54848"
]

def test_recipe_parser(url: str, backend_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """Test a single recipe URL"""
    try:
        response = httpx.post(
            f"{backend_url}/parse",
            json={"url": url},
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            recipe = data.get('recipe', {})
            return {
                "url": url,
                "status": "success",
                "title": recipe.get('title', 'N/A'),
                "ingredients_count": len(recipe.get('ingredients', [])),
                "instructions_count": len(recipe.get('instructions', [])),
                "has_nutrition": bool(recipe.get('nutrition')),
                "has_image": bool(recipe.get('image_url')),
                "fields_extracted": sum([
                    bool(recipe.get('title')),
                    bool(recipe.get('description')),
                    bool(recipe.get('servings')),
                    bool(recipe.get('prep_time')),
                    bool(recipe.get('cook_time')),
                    bool(recipe.get('total_time')),
                    bool(recipe.get('ingredients')),
                    bool(recipe.get('instructions')),
                    bool(recipe.get('nutrition')),
                    bool(recipe.get('image_url')),
                    bool(recipe.get('author')),
                    bool(recipe.get('ratings')),
                ])
            }
        else:
            error_data = response.json()
            return {
                "url": url,
                "status": "failed",
                "error": error_data.get('detail', 'Unknown error'),
                "status_code": response.status_code
            }
    except Exception as e:
        return {
            "url": url,
            "status": "error",
            "error": str(e)
        }

def main():
    print("🧪 Testing Recipe Parser Backend with Various Sites")
    print("=" * 60)
    
    # Check if backend is running
    try:
        health_response = httpx.get("http://localhost:8000/health", timeout=5.0)
        if health_response.status_code == 200:
            print("✅ Backend is running")
        else:
            print("❌ Backend health check failed")
            return
    except:
        print("❌ Backend is not running. Please start it first.")
        return
    
    print("\nTesting recipe extraction from popular sites:")
    print("-" * 60)
    
    results = []
    for i, url in enumerate(TEST_URLS, 1):
        print(f"\n[{i}/{len(TEST_URLS)}] Testing: {url.split('/')[2]}")
        result = test_recipe_parser(url)
        results.append(result)
        
        if result['status'] == 'success':
            print(f"  ✅ Success: {result['title'][:50]}...")
            print(f"     - Ingredients: {result['ingredients_count']}")
            print(f"     - Instructions: {result['instructions_count']}")
            print(f"     - Fields extracted: {result['fields_extracted']}/12")
            print(f"     - Has nutrition: {result['has_nutrition']}")
            print(f"     - Has image: {result['has_image']}")
        elif result['status'] == 'failed':
            print(f"  ⚠️  Failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"  ❌ Error: {result.get('error', 'Unknown error')}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] in ['failed', 'error']]
    
    print(f"✅ Successful: {len(successful)}/{len(TEST_URLS)}")
    print(f"❌ Failed: {len(failed)}/{len(TEST_URLS)}")
    
    if successful:
        avg_fields = sum(r['fields_extracted'] for r in successful) / len(successful)
        print(f"📊 Average fields extracted: {avg_fields:.1f}/12")
    
    if failed:
        print("\nFailed sites:")
        for r in failed:
            print(f"  - {r['url'].split('/')[2]}: {r.get('error', 'Unknown')}")
    
    print("\n✨ Test complete!")

if __name__ == "__main__":
    main()
