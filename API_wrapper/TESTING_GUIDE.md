# Testing Guide - Running Without API Key

## Application is Now Running! ✅

Your Animal Encyclopedia API is live at:
- **Main URL**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## Quick Status Check

✅ Application started successfully
✅ Health endpoint working
✅ API documentation available
✅ All endpoints accessible

---

## What You Can Access Now

### 1. Interactive API Documentation (Swagger UI)
**Open in browser**: http://localhost:8000/docs

This gives you:
- Interactive API playground
- Try out endpoints with sample data
- See request/response formats
- Test all endpoints

### 2. Health Check
```bash
curl http://localhost:8000/health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-06T00:00:00Z"
}
```

### 3. Root Endpoint
```bash
curl http://localhost:8000/
```

**Response**:
```json
{
  "name": "Animal Encyclopedia AI",
  "version": "1.0.0",
  "status": "operational",
  "docs": "/docs"
}
```

---

## Testing With Queries (Without API Key)

### What Will Happen

When you send a query WITHOUT an API key:

✅ **Will Work**:
1. Request validation
2. Session creation
3. Embedding generation (LOCAL, FREE)
4. Semantic routing (classifies query)
5. Anaphora resolution (pronoun handling)
6. Semantic cache check

❌ **Will Fail**:
- Final LLM response generation (needs OpenAI API)

**Error you'll see**:
```
OpenAI API key is required for LLM responses
```

---

## Test Queries via Swagger UI (Recommended)

### Step 1: Open Swagger UI
Go to: http://localhost:8000/docs

### Step 2: Find the `/api/v1/query` Endpoint
Click on **POST /api/v1/query**

### Step 3: Click "Try it out"

### Step 4: Enter Test Query
```json
{
  "query": "How many hearts does an octopus have?",
  "skip_cache": false
}
```

### Step 5: Click "Execute"

### Expected Response (Without API Key):
```json
{
  "session_id": "auto-generated-uuid",
  "error": "OpenAI API key is required for LLM responses",
  "metadata": {
    "response_time_ms": 150,
    "timestamp": "2026-01-07T..."
  }
}
```

**But before the error**, the system successfully:
- ✅ Generated embedding (LOCAL model)
- ✅ Routed the query (detected it's about animals)
- ✅ Checked semantic cache
- ✅ Prepared context

---

## Test Queries via curl

### Query 1: Animal Question (Should Accept)
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "How many hearts does an octopus have?"}'
```

### Query 2: Non-Animal Question (Should Reject)
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "How does the internet work?"}'
```

**Expected Response** (This should work fully WITHOUT API key):
```json
{
  "session_id": "auto-generated-uuid",
  "query": {
    "original": "How does the internet work?",
    "resolved": "How does the internet work?",
    "anaphora_resolved": false
  },
  "routing": {
    "decision": "REJECT",
    "confidence": 0.35,
    "reason": "Non-animal query"
  },
  "response": {
    "answer": "I specialize exclusively in animal-related questions. Please ask me about any creature in Kingdom Animalia.",
    "source": "semantic_filter"
  },
  "metadata": {
    "response_time_ms": 50,
    "timestamp": "2026-01-07T..."
  }
}
```

**This response comes from the semantic router - NO API KEY NEEDED!**

---

## Test Statistics Endpoint

```bash
curl http://localhost:8000/api/v1/stats
```

**Expected Response**:
```json
{
  "router": {
    "accept_threshold": 0.72,
    "reject_threshold": 0.45,
    "anchor_count": 95,
    "negative_count": 110
  },
  "cache": {
    "hit_rate": 0.0,
    "total_hits": 0,
    "total_misses": 0,
    "size": 0
  },
  "active_sessions": 0
}
```

---

## Test Python Script

Create a file `test_api.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print("Health Check:", response.json())

def test_animal_query():
    """Test animal query (will fail at LLM without API key)"""
    response = requests.post(
        f"{BASE_URL}/api/v1/query",
        json={"query": "How many hearts does an octopus have?"}
    )
    print("\nAnimal Query Response:")
    print(json.dumps(response.json(), indent=2))

def test_non_animal_query():
    """Test non-animal query (should work fully)"""
    response = requests.post(
        f"{BASE_URL}/api/v1/query",
        json={"query": "How does photosynthesis work?"}
    )
    print("\nNon-Animal Query Response:")
    print(json.dumps(response.json(), indent=2))

def test_stats():
    """Test stats endpoint"""
    response = requests.get(f"{BASE_URL}/api/v1/stats")
    print("\nStats:")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_health()
    test_non_animal_query()  # This should work fully
    test_animal_query()  # This will fail at LLM step
    test_stats()
```

Run it:
```bash
python test_api.py
```

---

## What's Actually Working (Behind the Scenes)

Even without the API key, here's what's happening:

### For Every Query:
1. **Request Processing** ✅
   - JSON validation
   - Session management

2. **Embedding Generation** ✅ (FREE LOCAL MODEL)
   - Your query is converted to a 384-dim vector
   - Uses sentence-transformers
   - Cost: $0.00

3. **Semantic Routing** ✅
   - Compares your query embedding to 95 positive anchors
   - Compares to 110 negative anchors
   - Decides: ACCEPT or REJECT
   - Cost: $0.00

4. **Anaphora Resolution** ✅
   - Checks for pronouns ("it", "they", etc.)
   - Looks back in conversation history
   - Replaces pronouns with animal names
   - Cost: $0.00

5. **Semantic Cache Check** ✅
   - Searches for similar past queries
   - Uses FAISS vector similarity
   - Cost: $0.00

6. **LLM Response** ❌ (Needs API Key)
   - Would call OpenAI gpt-4o-mini
   - Would cost ~$0.001 per query

---

## When You Add the API Key

Simply edit `.env`:
```bash
OPENAI_API_KEY=sk-proj-your-actual-key
```

Then **restart the application**:
```bash
# Press Ctrl+C in the terminal where it's running
# Then run again:
uvicorn animal_encyclopedia.api.app:app --reload --host 0.0.0.0 --port 8000
```

---

## Stop the Application

To stop the server:
1. Find the terminal where it's running
2. Press **Ctrl+C**

Or if running in background:
```bash
# Find the process
tasklist | findstr python

# Kill it
taskkill /PID <process-id> /F
```

---

## Next Steps

### Without API Key:
- ✅ Test semantic routing (works perfectly)
- ✅ Explore API documentation
- ✅ Understand the architecture
- ✅ Test non-animal queries (fully functional)
- ✅ Check statistics endpoint

### With API Key:
- Test full end-to-end queries
- Test conversation history
- Test semantic caching
- Monitor API costs
- Tune thresholds

---

## Useful Commands Summary

```bash
# Start the application
uvicorn animal_encyclopedia.api.app:app --reload

# Test health
curl http://localhost:8000/health

# Test query
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What do elephants eat?"}'

# View stats
curl http://localhost:8000/api/v1/stats

# Open docs
# Go to: http://localhost:8000/docs
```

---

## What to Explore

1. **Swagger UI** (http://localhost:8000/docs)
   - Most user-friendly way to test
   - See all available endpoints
   - Interactive testing

2. **ReDoc** (http://localhost:8000/redoc)
   - Alternative documentation format
   - Better for reading/understanding

3. **Code**
   - `animal_encyclopedia/core/semantic_router.py` - See how routing works
   - `animal_encyclopedia/core/orchestrator.py` - Main pipeline
   - `config/settings.py` - All configuration

---

**The system is fully operational for testing the routing and embedding logic!**

Enjoy exploring! 🎉
