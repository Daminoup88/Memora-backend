# Memora backend

API of the Memora project using FastAPI.

## Getting Started

### Prerequisites

Docker: [Using Docker](#installation-with-docker) (recommended)

OR

- [Python 3.10+](https://www.python.org/downloads/)
- [PostgreSQL](https://www.postgresql.org/download/) with [pgvector extension](https://github.com/pgvector/pgvector#installation)
- [Ollama](https://ollama.com/download)

### Installation with Docker
See [Installation without Docker](#installation-without-docker-tested-on-windows) below.

1. Make sure you have a docker engine such as [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

2. Clone the repository

```bash
git clone https://github.com/Lucari00/Memora-backend.git
```

3. Navigate to the project directory

```bash
cd Memora-backend
```


4. Create a `.env` file from the example one:

```bash
cp .env.example .env
```

5. **IMPORTANT**: Edit the `.env` file and set strong secrets (especially POSTGRES_PASSWORD and TOKEN_SECRET_KEY). You can generate a secure secret key using Python:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

6. You can add the LLM features by setting LLM_ENABLED to True.

7. Build and start:

- In **PRODUCTION**:

```bash
docker compose up -d --build
```

or, with the legacy docker-compose executable:

```bash
docker-compose -f compose.yaml up -d --build
```

- For **DEVELOPMENT**:

```bash
docker compose -f compose-dev.yaml up -d --build
```

or, with the legacy docker-compose executable:

```bash
docker-compose -f compose-dev.yaml up -d --build
```


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

6. Create a `.env` file from the example one:

```bash
cp .env.example .env
```

5. **IMPORTANT**: Edit the `.env` file and set strong secrets (especially POSTGRES_PASSWORD and TOKEN_SECRET_KEY). You can generate a secure secret key using Python:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

6. If you have [Ollama](https://ollama.com/download) installed You can add the LLM features by setting LLM_ENABLED to True.

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