# MoonAI-Parser

## Getting Started

### Prerequisites
- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd MoonAI-Parser
   ```

2. **Start all services:**
   ```bash
   docker compose up --build
   ```

3. **Access the API:**
   - FastAPI docs: [http://localhost:8002/docs](http://localhost:8002/docs)

---

## Useful Commands

You can use the Makefile for common development tasks:

- **Format code:**
  ```bash
  make format
  ```
- **Check code formatting:**
  ```bash
  make format_check
  ```
- **Run static analysis (flake8, mypy):**
  ```bash
  make static
  ```
- **Run tests with coverage:**
  ```bash
  make test
  ```
- **Run the app locally:**
  ```bash
  make run
  ```
- **Create a new migration:**
  ```bash
  make migrations message="<your message>"
  ```
- **Apply migrations:**
  ```bash
  make migrate
  ```
