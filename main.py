from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from recipe_scrapers import scrape_me, scrape_html
from urllib.parse import urlparse
import httpx
import uuid
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
import re
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_iso_duration(duration_str):
    """Parse ISO 8601 duration format (e.g., PT5M) to human-readable format"""
    if not duration_str:
        return None
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?', duration_str)
    if match:
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        total_minutes = hours * 60 + minutes
        if total_minutes > 0:
            return f"{total_minutes} minutes"
    return None

app = FastAPI(
    title="Dishly.pro Recipe Parser API",
    description="Clean recipe scraping service for Dishly.pro",
    version="1.0.0"
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Request/Response Models
class RecipeParseRequest(BaseModel):
    url: HttpUrl

class RecipeData(BaseModel):
    """Comprehensive recipe data model with all available fields"""
    id: str
    title: str
    description: Optional[str] = None
    servings: Optional[int] = None
    yields: Optional[str] = None
    cook_time: Optional[str] = None
    prep_time: Optional[str] = None
    total_time: Optional[str] = None
    ingredients: List[str] = Field(default_factory=list)
    instructions: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    nutrition: Optional[Dict[str, Any]] = None
    source_url: str
    source_name: str
    video_url: Optional[str] = None
    has_video: bool = False
    image_url: Optional[str] = None
    author: Optional[str] = None
    ratings: Optional[float] = None
    ratings_count: Optional[int] = None
    cuisine: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[List[str]] = None
    language: Optional[str] = None
    dietary_restrictions: Optional[List[str]] = None

class RecipeParseResponse(BaseModel):
    """Response from recipe parsing"""
    recipe_id: str = Field(..., description="Unique recipe ID")
    recipe: RecipeData
    message: Optional[str] = None

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Dishly.pro Recipe Parser API is running"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "recipe-parser",
        "version": "1.0.0"
    }

# In-memory storage for parsed recipes (for demo purposes)
recipes_db: Dict[str, Dict[str, Any]] = {}
recipe_storage: Dict[str, RecipeData] = {}

@app.post("/parse", response_model=RecipeParseResponse)
async def parse_recipe(request: RecipeParseRequest):
    """
    Parse a recipe from a given URL using recipe-scrapers
    """
    url = str(request.url)
    recipe_id = str(uuid.uuid4())
    
    logger.info(f"Parsing recipe from URL: {url}")
    
    try:
        # First, fetch the page content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = httpx.get(url, headers=headers, timeout=30, follow_redirects=True)
        response.raise_for_status()
        html_content = response.text
        
        # Use recipe-scrapers with the HTML content
        scraper = None
        json_ld_data = None
        
        # First, try to extract JSON-LD data as fallback
        json_ld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
        json_ld_matches = re.findall(json_ld_pattern, html_content, re.DOTALL | re.IGNORECASE)
        for match in json_ld_matches:
            try:
                data = json.loads(match)
                # Handle both single objects and arrays
                if isinstance(data, list):
                    for item in data:
                        if '@type' in item and ('Recipe' in item.get('@type', []) if isinstance(item.get('@type'), list) else item.get('@type') == 'Recipe'):
                            json_ld_data = item
                            break
                elif '@type' in data and ('Recipe' in data.get('@type', []) if isinstance(data.get('@type'), list) else data.get('@type') == 'Recipe'):
                    json_ld_data = data
                if json_ld_data:
                    logger.info("Found recipe data in JSON-LD")
                    break
            except json.JSONDecodeError:
                continue
        
        try:
            # Try scraping with HTML content directly
            scraper = scrape_html(html=html_content, org_url=url, wild_mode=False)
        except Exception as e:
            logger.warning(f"Standard HTML scraping failed, trying wild mode: {e}")
            try:
                scraper = scrape_html(html=html_content, org_url=url, wild_mode=True)
            except Exception as e2:
                logger.warning(f"Wild mode HTML scraping failed, trying URL scraping: {e2}")
                try:
                    scraper = scrape_me(url, wild_mode=True)
                except Exception as e3:
                    logger.error(f"All scraping methods failed: {e3}")
                    scraper = None
        
        # Extract basic recipe information
        title = None
        if scraper:
            try:
                title = scraper.title()
            except Exception as e:
                logger.warning(f"Could not extract title: {e}")
        
        if not title:
            # Try to extract from URL as fallback
            url_parts = url.split('/')[-1].replace('-', ' ').replace('_', ' ')
            title = re.sub(r'\d+', '', url_parts).replace('recipe', '').strip().title()
            if not title:
                title = "Recipe from " + urlparse(url).netloc.replace('www.', '')
        
        # Extract all available recipe data using recipe-scrapers methods
        # Get ingredients - try multiple methods
        ingredients = []
        if scraper:
            try:
                ingredients = scraper.ingredients()
                if not ingredients:
                    logger.warning(f"No ingredients found for {url}")
            except Exception as e:
                logger.warning(f"Error getting ingredients: {e}")
        
        # Fallback to JSON-LD data if available
        if not ingredients and json_ld_data and 'recipeIngredient' in json_ld_data:
            ingredients = json_ld_data['recipeIngredient']
            logger.info(f"Using ingredients from JSON-LD: {len(ingredients)} items")
        
        # Get instructions - try multiple methods
        instructions = []
        if scraper:
            try:
                # First try to get as list
                instructions = scraper.instructions_list()
            except:
                try:
                    # Fall back to string instructions
                    instructions_str = scraper.instructions()
                    if instructions_str:
                        # Split by common patterns
                        # Split by numbered steps, double newlines, or periods followed by capital letters
                        instructions = re.split(r'(?:\d+[.)\s]+|\n\n+|(?<=\.)\s+(?=[A-Z]))', instructions_str)
                        instructions = [inst.strip() for inst in instructions if inst.strip() and len(inst.strip()) > 10]
                except Exception as e:
                    logger.warning(f"Error getting instructions: {e}")
        
        # Fallback to JSON-LD data if available
        if not instructions and json_ld_data and 'recipeInstructions' in json_ld_data:
            json_instructions = json_ld_data['recipeInstructions']
            instructions = []
            for inst in json_instructions:
                if isinstance(inst, dict) and 'text' in inst:
                    instructions.append(inst['text'])
                elif isinstance(inst, str):
                    instructions.append(inst)
            logger.info(f"Using instructions from JSON-LD: {len(instructions)} steps")
        
        # Don't fail if we can't get all data - just warn
        if not ingredients:
            logger.warning(f"No ingredients found for {url}")
            ingredients = ["Please check the original recipe for ingredients"]
        if not instructions:
            logger.warning(f"No instructions found for {url}")
            instructions = ["Please check the original recipe for instructions"]
        
        # Extract ALL available fields from recipe-scrapers
        # Description
        description = None
        if scraper:
            try:
                description = scraper.description()
            except:
                pass
        
        # Yields/Servings
        servings = None
        yields = None
        if scraper:
            try:
                yields = scraper.yields()
                if yields:
                    # Extract number from yields string
                    match = re.search(r'\d+', str(yields))
                    if match:
                        servings = int(match.group())
            except:
                pass
        
        # Fallback to JSON-LD data
        if not yields and json_ld_data:
            if 'recipeYield' in json_ld_data:
                yields = str(json_ld_data['recipeYield'])
                match = re.search(r'\d+', yields)
                if match:
                    servings = int(match.group())
        
        # Timing information
        cook_time = None
        prep_time = None
        total_time = None
        if scraper:
            try:
                time_val = scraper.cook_time()
                if time_val:
                    cook_time = f"{time_val} minutes" if isinstance(time_val, (int, float)) else str(time_val)
            except:
                pass
            
            try:
                time_val = scraper.prep_time()
                if time_val:
                    prep_time = f"{time_val} minutes" if isinstance(time_val, (int, float)) else str(time_val)
            except:
                pass
            
            try:
                time_val = scraper.total_time()
                if time_val:
                    total_time = f"{time_val} minutes" if isinstance(time_val, (int, float)) else str(time_val)
            except:
                pass
        
        # Fallback to JSON-LD data
        if json_ld_data:
            if not prep_time and 'prepTime' in json_ld_data:
                prep_time = parse_iso_duration(json_ld_data['prepTime'])
            if not cook_time and 'cookTime' in json_ld_data:
                cook_time = parse_iso_duration(json_ld_data['cookTime'])
            if not total_time and 'totalTime' in json_ld_data:
                total_time = parse_iso_duration(json_ld_data['totalTime'])
        
        # Nutrition information
        nutrition = {}
        if scraper:
            try:
                nutrients = scraper.nutrients()
                if nutrients:
                    nutrition = {
                        "calories": nutrients.get("calories"),
                        "protein": nutrients.get("proteinContent"),
                        "carbs": nutrients.get("carbohydrateContent"),
                        "fat": nutrients.get("fatContent"),
                        "sugar": nutrients.get("sugarContent"),
                        "sodium": nutrients.get("sodiumContent"),
                        "fiber": nutrients.get("fiberContent"),
                        "cholesterol": nutrients.get("cholesterolContent"),
                        "saturatedFat": nutrients.get("saturatedFatContent")
                    }
                    # Remove None values
                    nutrition = {k: v for k, v in nutrition.items() if v is not None}
            except:
                pass
        
        # Media
        image_url = None
        video_url = None
        notes = None
        author = None
        ratings = None
        ratings_count = None
        cuisine = None
        category = None
        keywords = None
        language = None
        dietary_restrictions = None
        
        if scraper:
            try:
                image_url = scraper.image()
            except:
                pass
            
            try:
                video_url = scraper.video()
            except:
                pass
            
            try:
                notes = scraper.notes()
            except:
                pass
            
            try:
                author = scraper.author()
            except:
                pass
            
            try:
                ratings = scraper.ratings()
            except:
                pass
            try:
                ratings_count = scraper.ratings_count()
            except:
                pass
            
            try:
                cuisine = scraper.cuisine()
            except:
                pass
            
            try:
                category = scraper.category()
            except:
                pass
            
            try:
                keywords = scraper.keywords()
            except:
                pass
            
            try:
                language = scraper.language()
            except:
                pass
            
            try:
                dietary_restrictions = scraper.dietary_restrictions()
            except:
                pass
        
        # Get source information
        source_name = urlparse(url).netloc.replace('www.', '')
        
        # Create comprehensive recipe object with all extracted data
        recipe = RecipeData(
            id=recipe_id,
            title=title,
            description=description,
            servings=servings,
            yields=yields,
            cook_time=cook_time,
            prep_time=prep_time,
            total_time=total_time,
            ingredients=ingredients,
            instructions=instructions,
            notes=notes,
            nutrition=nutrition if nutrition else None,
            source_url=url,
            source_name=source_name,
            video_url=video_url,
            has_video=bool(video_url),
            image_url=image_url,
            author=author,
            ratings=ratings,
            ratings_count=ratings_count,
            cuisine=cuisine,
            category=category,
            keywords=keywords,
            language=language,
            dietary_restrictions=dietary_restrictions
        )
        
        logger.info(f"Successfully parsed recipe: {title}")
        
        # Store the recipe for later retrieval
        recipe_storage[recipe_id] = recipe
        
        # Return the parsed recipe
        return RecipeParseResponse(
            recipe_id=recipe_id,
            recipe=recipe,
            message="Recipe parsed successfully"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error accessing {url}: {e}")
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=400,
                detail="Recipe not found at this URL. Please check the link and try again."
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unable to access the recipe website (HTTP {e.response.status_code}). Please check the URL and try again."
            )
    except httpx.TimeoutException:
        logger.error(f"Timeout accessing {url}")
        raise HTTPException(
            status_code=400,
            detail="The recipe website took too long to respond. Please try again later."
        )
    except httpx.RequestError as e:
        logger.error(f"Network error accessing {url}: {e}")
        raise HTTPException(
            status_code=400,
            detail="Unable to connect to the recipe website. Please check your internet connection and try again."
        )
    except Exception as e:
        error_message = str(e).lower()
        logger.error(f"Error parsing {url}: {error_message}")
        
        # Try to return partial data instead of failing completely
        try:
            # Extract title from URL
            title = url.split('/')[-1].replace('-', ' ').title() if url else "Recipe"
            # Remove common suffixes
            title = title.replace('.html', '').replace('.htm', '').replace('Recipe', '').strip()
            if not title:
                title = "Recipe from " + urlparse(url).netloc
            
            # Create a minimal recipe with what we have
            recipe = RecipeData(
                id=recipe_id,
                title=title,
                description="Unable to fully parse this recipe. Please visit the original site for complete details.",
                source_url=url,
                source_name=urlparse(url).netloc.replace('www.', ''),
                ingredients=["Unable to extract ingredients - please check the original recipe"],
                instructions=["Unable to extract instructions - please check the original recipe"]
            )
            
            # Store the recipe
            recipe_storage[recipe_id] = recipe
            
            return RecipeParseResponse(
                recipe_id=recipe_id,
                recipe=recipe,
                message="Partial recipe data extracted. Some information may be missing."
            )
        except:
            # If even that fails, return a proper error
            raise HTTPException(
                status_code=400,
                detail="Unable to extract recipe from this website. The page might not contain a properly formatted recipe, or the site might be temporarily unavailable."
            )

@app.get("/recipe/{recipe_id}")
async def get_recipe(recipe_id: str):
    """
    Retrieve a previously parsed recipe by ID
    """
    if recipe_id not in recipe_storage:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found"
        )
    
    return recipe_storage[recipe_id]

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "An unexpected error occurred",
            "details": str(exc)
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
