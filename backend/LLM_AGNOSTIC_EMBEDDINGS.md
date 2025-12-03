# LLM-Agnostic Embeddings Service

## Overview

The embeddings service now supports **multiple LLM providers** with automatic provider detection:

- ✅ **Google Gemini** (Primary - text-embedding-004)
- ✅ **OpenAI** (Fallback - text-embedding-3-small)
- ✅ **Mock** (Development/Testing)

## Configuration

### Using Gemini (Recommended)

Add to `.env`:
```bash
GOOGLE_API_KEY=your-gemini-api-key-here
```

### Using OpenAI

Add to `.env`:
```bash
OPENAI_API_KEY=sk-your-openai-key-here
```

### Provider Priority

The service automatically detects which provider to use:

1. **Gemini** - If `GOOGLE_API_KEY` is set
2. **OpenAI** - If `OPENAI_API_KEY` is set (and no Gemini key)
3. **Mock** - If no API keys configured (development)

## API Details

### Gemini Embeddings

- **Model**: `text-embedding-004`
- **Dimensions**: 768 (auto-detected)
- **Endpoint**: `https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent`
- **Authentication**: API key in query params

**Request Format**:
```json
{
  "model": "models/text-embedding-004",
  "content": {
    "parts": [{
      "text": "Your text here"
    }]
  }
}
```

**Response Format**:
```json
{
  "embedding": {
    "values": [0.123, -0.456, ...]
  }
}
```

### OpenAI Embeddings

- **Model**: `text-embedding-3-small`
- **Dimensions**: 1536 (auto-detected)
- **Endpoint**: `https://api.openai.com/v1/embeddings`
- **Authentication**: Bearer token in headers

**Request Format**:
```json
{
  "input": "Your text here",
  "model": "text-embedding-3-small"
}
```

**Response Format**:
```json
{
  "data": [{
    "embedding": [0.123, -0.456, ...]
  }]
}
```

### Mock Embeddings

- **Dimensions**: 768 (configurable)
- **Method**: SHA-256 hash-based deterministic generation
- **Use Case**: Development and testing without API costs

## Usage

The service is completely transparent - you don't need to specify the provider:

```python
from app.services.embeddings_service import get_embeddings_service

# Get service (auto-detects provider)
embeddings_service = get_embeddings_service()

# Generate embedding (uses configured provider)
embedding = await embeddings_service.generate_embedding("Your text here")

# Add knowledge with embedding
result = await embeddings_service.add_knowledge_with_embedding(
    customer_id="customer-123",
    content="Our product helps businesses automate workflows",
    content_type="text"
)

# Search similar knowledge (RAG)
results = await embeddings_service.search_similar_knowledge(
    customer_id="customer-123",
    query="What does the product do?",
    limit=5,
    similarity_threshold=0.7
)
```

## Provider Detection Logic

```python
def _detect_provider(self) -> str:
    """Auto-detect which LLM provider to use"""
    if hasattr(settings, 'GOOGLE_API_KEY') and settings.GOOGLE_API_KEY:
        return "gemini"
    elif hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
        return "openai"
    else:
        logger.warning("No LLM API key configured, using mock embeddings")
        return "mock"
```

## Error Handling

The service includes robust fallback mechanisms:

1. **Primary Provider Fails** → Falls back to mock embeddings
2. **API Rate Limit** → Returns mock embeddings with warning
3. **Network Error** → Returns mock embeddings with error log

This ensures the system never crashes due to embedding generation failures.

## Extending to Other Providers

To add a new provider (e.g., Anthropic, Cohere):

1. Add API key to `config.py`:
```python
COHERE_API_KEY: str = ""
```

2. Update `_detect_provider()`:
```python
def _detect_provider(self) -> str:
    if hasattr(settings, 'COHERE_API_KEY') and settings.COHERE_API_KEY:
        return "cohere"
    # ... existing logic
```

3. Add provider method:
```python
async def _generate_cohere_embedding(self, text: str) -> Optional[List[float]]:
    """Generate embedding using Cohere API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.cohere.ai/v1/embed",
                headers={
                    "Authorization": f"Bearer {settings.COHERE_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "texts": [text],
                    "model": "embed-english-v3.0"
                }
            )
            result = response.json()
            return result["embeddings"][0]
    except Exception as e:
        logger.error(f"Cohere embedding failed: {e}")
        raise
```

4. Update `generate_embedding()`:
```python
if self.provider == "cohere":
    return await self._generate_cohere_embedding(text)
```

## Testing

### Test with Gemini
```bash
# Set Gemini API key
export GOOGLE_API_KEY=your-key

# Test
curl -X POST http://localhost:8000/api/knowledge \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test content", "content_type": "text"}'
```

### Test with Mock (No API Key)
```bash
# Unset all API keys
unset GOOGLE_API_KEY
unset OPENAI_API_KEY

# Test - will use mock embeddings
curl -X POST http://localhost:8000/api/knowledge \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test content", "content_type": "text"}'
```

## Performance Considerations

### Gemini
- **Latency**: ~200-500ms per embedding
- **Cost**: Free tier available, then pay-per-use
- **Dimensions**: 768 (smaller = faster similarity search)

### OpenAI
- **Latency**: ~100-300ms per embedding
- **Cost**: $0.00002 per 1K tokens
- **Dimensions**: 1536 (higher precision)

### Mock
- **Latency**: <1ms (instant)
- **Cost**: Free
- **Dimensions**: Configurable (default 768)

## Recommendations

1. **Production**: Use Gemini (better integration with Google ecosystem)
2. **Development**: Use Mock (fast, free, deterministic)
3. **Testing**: Use Mock with fixed seeds for reproducibility
4. **High Precision**: Use OpenAI (1536 dimensions)
5. **Cost Optimization**: Use Gemini (768 dimensions, good balance)

## Monitoring

The service logs provider selection and embedding generation:

```
INFO: Using provider: gemini
INFO: Generated Gemini embedding with 768 dimensions
```

Monitor these logs to ensure the correct provider is being used.
