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
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# API
API_KEY=your-api-key-here

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1
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
celery -A app.tasks.celery_app worker --loglevel=info
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

## Docker Deployment

1. Build the Docker image:
```bash
docker build -t python-api-task .
```

2. Run the container:
```bash
docker run -p 8000:8000 --env-file .env python-api-task
```

## Project Structure

```
python-api-task/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── routes.py
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   ├── database.py
│   │   └── models.py
│   ├── services/
│   │   ├── chutes.py
│   │   ├── datura.py
│   │   └── staking.py
│   ├── tasks/
│   │   └── background_tasks.py
│   └── main.py
├── .env.example
├── .gitignore
├── Dockerfile
├── requirements.txt
└── README.md
```