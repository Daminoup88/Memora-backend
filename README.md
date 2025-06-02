# SanteActive backend

API of the SanteActive project using FastAPI.

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL with pgvector extension
- Ollama

### Installation

1. Clone the repository

```bash
git clone https://github.com/Lucari00/SanteActive-backend.git
```

2. Setup a virtual environment

```bash
python -m venv .venv
```

3. Activate the virtual environment

```bash
.venv\Scripts\activate
```

4. Install the dependencies

```bash
pip install -r requirements.txt
```

5. Add the ".env" file in the root directory with your personal information:
  
```bash
DATABASE_DRIVER=postgresql
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=user
DATABASE_PASSWORD=password
DATABASE_NAME=database

TOKEN_SECRET_KEY=secret
TOKEN_ALGORITHM=HS256

PASSWORD_ALGORITHM=sha256_crypt
```

6. Run the server

```bash
fastapi run --reload --host 0.0.0.0 --port 8000
```

## Usage

The API documentation is available at `http://localhost:8000/docs`. To access the API from another device on the same network, replace `localhost` with the IP address of the host machine. Make sure the port is open and accessible to other devices.

## Testing

To run the tests and coverage, use the following command in the root directory:

```bash
pytest --cov=app --cov-report=html
```