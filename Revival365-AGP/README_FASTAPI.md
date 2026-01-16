# Revival365 AGP FastAPI Conversion

This project has been converted from an AWS Lambda function to a FastAPI application.

## Prerequisites

- Python 3.10+
- Access to the database (configured in `db/db_connection.py` and `config/config.ini`)

## Installation

1. Navigate to the `src` directory:
   ```bash
   cd src
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

> **Important**: The database connection in `src/db/db_connection.py` currently uses a private IP (`10.0.0.15`). 
> To run this locally, you must update the connection string in `src/db/db_connection.py` or ensure you have VPN access to the private network.
> The code also attempts to read `config/config.ini`.

## Running the Application

You can run the application using `uvicorn`:

```bash
uvicorn fastapi_app:app --reload
```
Or simply run the python script:
```bash
python fastapi_app.py
```

The server will start at `http://0.0.0.0:8000`.

## API Documentation

FastAPI automatically generates documentation:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Endpoints

### `POST /agp_profile`

Fetches glucose data profile.

**Request Body:**
```json
{
  "mobile_number": "+918521345464",
  "start_date": "2023-01-01", 
  "end_date": "2023-12-31"
}
```

**Response:**
Returns the glucose data JSON object.
