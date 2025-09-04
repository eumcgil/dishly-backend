# Dishly.pro Backend - Recipe Parser API

A FastAPI backend service that scrapes and parses recipes from URLs using the `recipe-scrapers` library.

## Features

- 🔍 **Recipe Scraping**: Extract recipes from 500+ supported websites
- 🚀 **FastAPI**: Modern, fast web framework with automatic API docs
- 🌐 **CORS Enabled**: Ready for frontend integration
- 📊 **Structured Data**: Returns clean, structured JSON
- 🛡️ **Error Handling**: Comprehensive error handling and logging
- 🐳 **Docker Ready**: Containerized for easy deployment

## API Endpoints

### `POST /parse`
Parse a recipe from a URL.

**Request:**
```json
{
  "url": "https://example.com/recipe"
}
```

**Response:**
```json
{
  "id": "uuid-string",
  "recipe": {
    "id": "uuid-string",
    "title": "Recipe Title",
    "description": "Recipe description",
    "servings": 4,
    "prep_time": "15 minutes",
    "cook_time": "30 minutes",
    "total_time": "45 minutes",
    "ingredients": ["ingredient 1", "ingredient 2"],
    "instructions": ["step 1", "step 2"],
    "notes": null,
    "nutrition": {
      "calories": 250,
      "protein": "10g",
      "carbs": "30g",
      "fat": "8g"
    },
    "source_url": "https://example.com/recipe",
    "source_name": "example.com"
  }
}
```

### `GET /health`
Health check endpoint.

### `GET /`
Root endpoint with service information.

### `GET /docs`
Interactive API documentation (Swagger UI).

## Supported Websites

This API uses the `recipe-scrapers` library which supports 500+ recipe websites including:

- AllRecipes
- Food Network
- Bon Appétit
- Taste of Home
- BBC Good Food
- Serious Eats
- And many more...

## Quick Start

### Local Development

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server:**
   ```bash
   uvicorn main:app --reload
   ```

4. **Test the API:**
   ```bash
   python test_api.py
   ```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

### Docker Deployment

1. **Build the image:**
   ```bash
   docker build -t dishly-backend .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 dishly-backend
   ```

## Deployment

### Railway

1. Connect your repository to Railway
2. The `railway.json` configuration will handle the deployment
3. Set environment variables if needed

### Render

1. Connect your repository to Render
2. Use the following settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Heroku

1. Create a new Heroku app
2. The `Procfile` is already configured
3. Deploy using Git or GitHub integration

## Environment Variables

The API supports these environment variables:

- `PORT`: Server port (default: 8000)
- `HOST`: Server host (default: 0.0.0.0)
- `LOG_LEVEL`: Logging level (default: INFO)
- `CORS_ORIGINS`: Allowed CORS origins (comma-separated)

## Frontend Integration

### Next.js Example

```typescript
async function parseRecipe(url: string) {
  const response = await fetch('http://localhost:8000/parse', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    throw new Error('Failed to parse recipe');
  }

  return response.json();
}
```

### React Example

```javascript
const [recipe, setRecipe] = useState(null);
const [loading, setLoading] = useState(false);

const handleSubmit = async (url) => {
  setLoading(true);
  try {
    const response = await fetch('http://localhost:8000/parse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });
    
    const data = await response.json();
    setRecipe(data.recipe);
  } catch (error) {
    console.error('Error:', error);
  } finally {
    setLoading(false);
  }
};
```

## Error Handling

The API returns appropriate HTTP status codes:

- **200**: Success
- **400**: Bad request (invalid URL, unsupported site, parsing failed)
- **422**: Validation error (invalid request format)
- **500**: Internal server error

Error responses include details:
```json
{
  "error": "Could not parse recipe from the provided URL",
  "details": "Additional error information"
}
```

## Testing

Run the test script to verify all endpoints:

```bash
python test_api.py
```

The test script will:
- Check health and root endpoints
- Test recipe parsing with known URLs
- Display results and API information

## Development

### Adding New Features

1. Update the Pydantic models in `main.py`
2. Add new endpoints following FastAPI patterns
3. Update tests and documentation

### Debugging

Enable debug logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

View logs in real-time:
```bash
uvicorn main:app --reload --log-level debug
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
