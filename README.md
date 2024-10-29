# SanteActive backend

API of the SanteActive project using FastAPI.

## Getting Started

### Prerequisites

- Python 3.10+

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
source .venv/Scripts/activate
```

4. Install the dependencies

```bash
pip install -r requirements.txt
```

5. Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Usage

The API documentation is available at `http://localhost:8000/docs`. To access the API from another device on the same network, replace `localhost` with the IP address of the host machine. Make sure the port is open and accessible to other devices.