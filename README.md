# Python API Task

A FastAPI-based application for managing Bittensor dividends, sentiment analysis, and staking operations.

## Features

- Fetch and manage Bittensor dividends
- Sentiment analysis of tweets
- Automated staking based on sentiment
- Redis caching for improved performance
- Celery background tasks for async operations
- SQLAlchemy async database operations

## Prerequisites

- Python 3.11+
- Redis
- PostgreSQL
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd python-api-task
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```
Edit the `.env` file with your configuration:
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PORT=6379

# API
API_KEY=your-api-key-here
DATURA_API_KEY=your-datura-api-key-here
CHUTES_API_KEY=your-chutes-api-key-here

# Bittensor
SUBTENSOR_NETWORK=finney
WALLET_HOTKEY=your-wallet-hotkey
WALLET_NETUID=your-wallet-netuid
WALLET_NAME=your-wallet-name

# PostgreSQL
POSTGRES_USER=your-postgres-user
POSTGRES_PASSWORD=your-postgres-password
POSTGRES_DB=your-postgres-db

# Cache
CACHE_EXPIRATION=120
```

## Database Setup

1. Create a PostgreSQL database:
```bash
createdb dbname
```

## Running the Application

1. Start Redis server:
```bash
redis-server
```

2. Start Celery worker:
```bash
celery -A app.core.celery_app worker --loglevel=info
```

3. Start the FastAPI application:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the application is running, you can access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### 1. Get All Dividends and Stakes Data

Retrieves all dividend and sentiment stake operation data from the database.

- **URL**: `/api/v1/get_all_dividends_stakes_data`
- **Method**: `GET`
- **Authentication**: Required (Bearer token), Format: {'Authorization': 'Bearer string_values_same_as_api_key_stored_in_env'}
- **Parameters**: None
- **Response**:
  ```json
  {
    "success": true,
    "dividends": [
      {
        "id": 1,
        "netuid": 1,
        "hotkey": "5FYYYY...",
        "amount": 0.5,
        "timestamp": "2023-01-01T12:00:00"
      }
    ],
    "sentiment_data": [
      {
        "id": 1,
        "netuid": 1,
        "hotkey": "5FYYYY...",
        "sentiment_score": 75,
        "amount": 7.5,
        "transaction_hash": "0x123...",
        "operation": "stake",
        "status": "completed",
        "created_at": "2023-01-01T12:00:00",
        "completed_at": "2023-01-01T12:01:00"
      }
    ]
  }
  ```

### 2. Get TAO Dividends

Retrieves TAO dividends for specified network UID and hotkey, with optional sentiment analysis and staking.

- **URL**: `/api/v1/tao_dividends`
- **Method**: `GET`
- **Authentication**: Required (Bearer token), Format: {'Authorization': 'Bearer string_values_same_as_api_key_stored_in_env'}
- **Parameters**:
  - `netuid` (optional): Network UID to query
  - `hotkey` (optional): Hotkey to query
  - `trade` (optional): Whether to trigger sentiment analysis and staking (default: false)
- **Response**:
  ```json
  {
    "success": true,
    "result": [
      {
        "netuid": 1,
        "hotkey": "5FYYYY...",
        "dividend": 0.5,
        "stake_tx_triggered": true,
        "cached": false
      }
    ]
  }
  ```

## Docker Deployment

1. Build the Docker image and start:
```bash
docker compose -f 'docker-compose.yml' up -d --build
```

2. To exit
```bash
docker compose -f 'docker-compose.yml' down
```

## Project Structure

```
python-api-task/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── routes.py         # API endpoints
│   ├── core/
│   │   ├── auth.py              # Authentication middleware
│   │   ├── celery_app.py        # Celery configuration
│   │   ├── config.py            # Application settings
│   │   └── logger.py            # Logging configuration
│   ├── db/
│   │   ├── database.py          # Database connection
│   │   ├── init_db.py           # Database initialization
│   │   └── models.py            # SQLAlchemy models
│   ├── services/
│   │   ├── bittensor_service.py # Bittensor network interaction
│   │   ├── chutes.py            # Sentiment analysis service
│   │   ├── datura.py            # Social media data service
│   │   └── staking.py           # Staking operations
│   ├── tasks/
│   │   └── background_tasks.py  # Celery background tasks
│   └── main.py                  # FastAPI application
├── .env.example                 # Example environment variables
├── .gitignore                   # Git ignore file
├── Dockerfile                   # Docker configuration
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```