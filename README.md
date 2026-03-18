
# Payment Processing Service

Backend service for processing orders and payments with bank integration.

## Features

- Order creation
- Payment processing
- Bank integration
- Partial refunds
- Background payment synchronization
- Asynchronous tasks

## Tech Stack

- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Celery
- Redis
- Pytest

## Project Structure

```text
.
├── README.md
├── alembic
│   ├── README
│   ├── env.py
│   ├── script.py.mako
│   └── versions
│       └── 89fcf89a2633_initial.py
├── alembic.ini
├── app
│   ├── __init__.py
│   ├── api
│   │   ├── __init__.py
│   │   ├── dependencies.py
│   │   └── routes
│   │       ├── __init__.py
│   │       ├── orders.py
│   │       └── payments.py
│   ├── config.py
│   ├── db
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── session.py
│   ├── exceptions.py
│   ├── integrations
│   │   └── bank_client.py
│   ├── main.py
│   ├── managers
│   │   └── payment_manager.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── bank_payment.py
│   │   ├── order.py
│   │   └── payment.py
│   ├── repositories
│   │   ├── __init__.py
│   │   ├── bank_payment_repository.py
│   │   ├── order_repository.py
│   │   └── payment_repository.py
│   ├── schemas
│   │   ├── __init__.py
│   │   ├── bank_api.py
│   │   ├── order.py
│   │   └── payment.py
│   ├── scripts
│   │   └── print_orders_payments.py
│   ├── services
│   │   ├── __init__.py
│   │   ├── bank_sync_service.py
│   │   ├── order_status_calculator.py
│   │   └── payment_service.py
│   ├── settings.py
│   └── tasks
│       ├── __init__.py
│       ├── celery_app.py
│       └── payment_tasks.py
├── docs
│   └── schema.png
├── mock_bank
│   └── main.py
├── requirements.txt
└── tests
    ├── __init__.py
    ├── e2e
    │   └── test_payments_e2e.py
    └── unit
        ├── test_bank_client.py
        ├── test_partial_refund.py
        └── test_payment_manager.py

20 directories, 49 files
```

## Database Schema

![Database schema](docs/schema.png)

## Installation

### 1. Clone repository

```bash
git clone https://github.com/a-lobanova/backend_test
cd backend_test
````

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create `.env` file:

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/my_db
REDIS_URL=redis://localhost:6379
```

### 5. Run migrations

```bash
alembic upgrade head
```

### 6. Start application

```bash
uvicorn app.main:app --reload
```

API will be available at:

```
http://localhost:8000
```

Swagger:

```
http://localhost:8000/docs
```

## Running Celery worker

```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

## Running tests

```bash
pytest
```

## API Endpoints

### Orders

```
POST /orders
GET /orders/{id}
```

### Payments

```
POST /payments
POST /payments/refund
```

## Architecture

The project follows a layered architecture:

```
API → Services → Managers → Repositories → Database
```

### Layers

* **API** – FastAPI routes
* **Services** – business logic
* **Managers** – complex payment workflows
* **Repositories** – database access layer
* **Integrations** – external bank API

## Background Jobs

Celery is used for asynchronous tasks:

* payment status synchronization with bank
* background processing


#TODO
## Tests

The project contains:

* unit tests
* end-to-end tests

* OrderService