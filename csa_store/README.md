# CSA Store

## Setup

1. Create virtual environment
2. Install dependencies

pip install -r requirements.txt

3. Copy environment file

cp .env.example .env

4. Run application

uvicorn app.main:app --reload

API:
http://localhost:8000

Swagger:
http://localhost:8000/docs
