# Memora backend

API of the Memora project using FastAPI.

## Getting Started

### Prerequisites

Docker: [Using Docker](#installation-with-docker) (recommended)

OR

- Python 3.10+
- PostgreSQL with pgvector extension
- Ollama

### Installation with Docker
See [Installation without Docker](#installation-without-docker-tested-on-windows) below.

1. Make sure you have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

2. Clone the repository

```bash
git clone https://github.com/Lucari00/Memora-backend.git
```

3. Navigate to the project directory

```bash
cd Memora-backend
```

For **development**, you can use the [`docker-compose-dev.yml`](docker-compose-dev.yml) file, which includes a PostgreSQL database and Ollama.

For **production**, file in construction for now.

4. Either create a `.env` file in the root directory with your personal information or add them in the docker compose file. It should contain the following information:

```bash
DATABASE_DRIVER=postgresql
DATABASE_PORT=5432
DATABASE_NAME=memora

TOKEN_SECRET_KEY=secret
TOKEN_ALGORITHM=HS256

PASSWORD_ALGORITHM=sha256_crypt

LLM_ENABLED=True
```

5. Change the secret key in the `.env` file to a strong, unique value. You can generate a secure secret key using Python:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

6. Replace `DATABASE_USER`, `DATABASE_PASSWORD`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` in the docker compose file with your personal information.

### Installation without Docker (tested on Windows)

1. Clone the repository

```bash
git clone https://github.com/Lucari00/Memora-backend.git
```

2. Navigate to the project directory

```bash
cd Memora-backend
```

3. Setup a virtual environment

```bash
python -m venv .venv
```

4. Activate the virtual environment

```bash
.venv\Scripts\activate
```

5. Install the dependencies

```bash
pip install -r requirements.txt
```

6. Add the ".env" file in the root directory with your personal information:
  
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

LLM_ENABLED=True
LLM_HOST=localhost
```

7. Run the server

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