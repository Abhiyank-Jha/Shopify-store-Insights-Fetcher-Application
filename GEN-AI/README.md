# Shopify Store Insights Fetcher

A FastAPI application for extracting comprehensive insights from Shopify stores.

## Features

- Product catalog extraction
- Hero products identification
- Policy analysis (privacy, return, refund)
- FAQ extraction
- Social media handles discovery
- Contact information extraction
- Important links identification
- Competitor analysis
- Data persistence with MySQL

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up MySQL database:
```bash
mysql -u root -padmin -e "CREATE DATABASE shopify_insights;"
```

4. Configure environment variables in `.env` file

## Usage

Start the server:
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Access the API documentation at: http://localhost:8000/docs

## API Endpoints

- `POST /api/v1/store-insights` - Extract store insights
- `POST /api/v1/competitor-analysis` - Analyze competitors
- `GET /api/v1/store-insights/{store_url}` - Get cached insights
- `GET /api/v1/store-insights` - Get all cached insights

## Example Request

```bash
curl -X POST "http://localhost:8000/api/v1/store-insights" \
  -H "Content-Type: application/json" \
  -d '{"website_url": "https://example-store.com"}'
``` 