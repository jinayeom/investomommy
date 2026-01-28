# InvestoMommy Backend

Your Personal Investment Companion - FastAPI Backend

## Features

- **Stock Search**: Search stocks by ticker symbol or company name using FMP API
- **Price Analysis**: View 30-day price charts and key price multiples (P/E, P/B, P/S, EV/EBITDA)
- **AI Insights**: Get AI-powered news sentiment analysis and valuation summaries using OpenAI
- **Virtual Portfolio**: Create and track paper trading investments with whole shares

## Project Structure

```
investomommy_backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py          # All API endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py          # Application settings
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py        # SQLAlchemy models
│   │   └── schemas.py         # Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py    # Authentication logic
│   │   ├── fmp_service.py     # FMP API integration
│   │   ├── openai_service.py  # OpenAI integration
│   │   └── portfolio_service.py # Portfolio management
│   ├── __init__.py
│   └── main.py                # FastAPI application
├── .env.example               # Environment variables template
├── .gitignore
├── requirements.txt
└── README.md
```

## API Endpoints

### Pages
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Landing page |
| GET | `/auth` | Auth page (login/signup options) |
| GET | `/health` | Health check |

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Register new user |
| POST | `/auth/login` | Login and get JWT token |
| GET | `/auth/me` | Get current user info |

### Dashboard (Requires Auth)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard` | Dashboard home |
| GET | `/dashboard/stocks/search?query=<term>` | Search stocks |
| GET | `/dashboard/stocks/{symbol}` | Get stock details with AI analysis |

### Portfolio (Requires Auth)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/portfolio` | Get portfolio summary |
| POST | `/dashboard/portfolio/holdings` | Add stock to portfolio |
| PATCH | `/dashboard/portfolio/holdings/{id}` | Update holding shares |
| DELETE | `/dashboard/portfolio/holdings/{id}` | Remove holding |

## Setup

### 1. Create Virtual Environment

```bash
cd investomommy_backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
- `FMP_API_KEY`: Get from [Financial Modeling Prep](https://financialmodelingprep.com/developer)
- `OPENAI_API_KEY`: Get from [OpenAI](https://platform.openai.com/api-keys)
- `SECRET_KEY`: Generate a secure random string for JWT signing

### 4. Run the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Usage Example

### 1. Sign Up
```bash
curl -X POST "http://localhost:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "investor1", "password": "securepass123"}'
```

### 2. Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=securepass123"
```

### 3. Search Stocks (with token)
```bash
curl -X GET "http://localhost:8000/dashboard/stocks/search?query=Apple" \
  -H "Authorization: Bearer <your_token>"
```

### 4. Get Stock Details
```bash
curl -X GET "http://localhost:8000/dashboard/stocks/AAPL" \
  -H "Authorization: Bearer <your_token>"
```

### 5. Add to Portfolio
```bash
curl -X POST "http://localhost:8000/dashboard/portfolio/holdings" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "shares": 10, "purchase_price": 185.50}'
```

## License

MIT
