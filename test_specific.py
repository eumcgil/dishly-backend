#!/usr/bin/env python3
"""
Test specific URLs to debug recipe-scrapers
"""
from recipe_scrapers import scrape_me
import httpx

test_urls = [
    "https://cooking.nytimes.com/recipes/1017997-seeded-pecan-granola",
    "https://www.allrecipes.com/cookie-butter-muddy-buddies-recipe-11799410"
]

for url in test_urls:
    print(f"\nTesting: {url}")
    print("-" * 60)
    try:
        # First test if we can fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = httpx.get(url, headers=headers, timeout=10, follow_redirects=True)
        print(f"HTTP Status: {response.status_code}")
        
        # Now try recipe-scrapers
        scraper = scrape_me(url)
        print(f"Title: {scraper.title()}")
        print(f"Ingredients count: {len(scraper.ingredients())}")
        print(f"Instructions: {len(scraper.instructions_list()) if hasattr(scraper, 'instructions_list') else 'N/A'}")
        print("✅ Success!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
