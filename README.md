# Memora backend

[![Running Tests](https://github.com/Daminoup88/Memora-backend/actions/workflows/python-app.yml/badge.svg)](https://github.com/Daminoup88/Memora-backend/actions/workflows/python-app.yml) [![Last Commit](https://img.shields.io/github/last-commit/Daminoup88/Memora-backend)](https://github.com/Daminoup88/Memora-backend/commits/main) [![Contributors](https://img.shields.io/github/contributors/Daminoup88/Memora-backend?color=brightgreen)](https://github.com/Daminoup88/Memora-backend/graphs/contributors)

API of the Memora project using FastAPI. The frontend app can be found here: **[Memora frontend](https://github.com/Daminoup88/Memora-frontend/)**.

*ESIEE Paris - 2024 - 4th year project*

## What is Memora?

Memora is a memory training mobile app designed for Alzheimer’s patients. It uses Spaced Retrieval Training (SRT, based on the Leitner system) to help exercise the brain with memories uploaded by relatives.

### **Contributors**: [Luca PALAYSI](https://github.com/Lucari00), [Tilad CHRAITEH](https://github.com/TiladC), [Paul MALLARD](https://github.com/mallardp), [Damien PHILIPPE](https://github.com/Daminoup88)

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
git clone https://github.com/Daminoup88/Memora-backend.git
```

3. Navigate to the project directory

```bash
cd Memora-backend
```


4. Create a `.env` file from the example one:

On Linux/Mac:

```bash
cp .env.example .env
```

On Windows:

```bash
copy .env.example .env
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
git clone https://github.com/Daminoup88/Memora-backend.git
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
