# GENEVA Score Calculator

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Revised Geneva Score for PE (Pulmonary Embolism) probability assessment.

- **Score Range:** 0-22 points with prevalence-calibrated tiers
- **Points-based scoring** with tiered action thresholds
- **Standard library only** for core calculation module (no external dependencies)
- **Multi-agent consensus system** with FastAPI REST interface

---

## ⚙️ Key Capabilities & Algorithmic Modules

### Core Calculation (`geneva.py`)
- **`calculate_score(present)`** — Calculate Geneva score from clinical factors
- **`assess_row(row)`** — Assess a CSV row and map columns to score factors
- **`process_csv(inp, out)`** — Batch process CSV files with patient data
- **`main(argv)`** — CLI entry point for single evaluations and batch processing

### Enterprise Features (`agents/`)
- **`agents/base.py`** — PHI Outbound Guard and HMAC-SHA256 Audit Trail
- **`agents/supervisor.py`** — Multi-agent consensus orchestrator
- **`agents/workers.py`** — Specialized QC, Safety, and Protocol Conformance workers
- **`agents/api.py`** — FastAPI REST API server

---

## 📐 Clinical Factors & Scoring

| Factor | Points |
|:-------|:-------|
| Hypotension | 1 |
| Tachycardia | 1 |
| Tachypnea | 1 |
| Fever | 1 |
| Altered Mental Status | 1 |

### Risk Tiers

| Score | Tier | Action |
|:------|:-----|:-------|
| 0-2 | Low | Standard workup |
| 3-4 | Moderate | Consider D-dimer testing |
| 5+ | High | Proceed to CTA/VQ scan |

---

## 💻 Installation

### Local Installation
```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/geneva-score-calculator.git
cd geneva-score-calculator

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install fastapi uvicorn pydantic pytest
```

### Docker Deployment
```bash
docker build -t geneva-score-calculator .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key geneva-score-calculator
```

Or using Docker Compose:
```bash
AUDIT_SECRET_KEY=your-secret-key docker-compose up
```

---

## 🔧 Usage

### Command Line Interface

#### 1. Single Patient Evaluation
```bash
python geneva.py single --age 68 --sex M
python geneva.py single --age 45 --sex F --hypotension 1 --tachycardia 1
```

#### 2. JSON Input
```bash
python geneva.py single --json '{"Hypotension": 1, "Tachycardia": 1, "Tachypnea": 1}'
```

#### 3. Batch CSV Processing
```bash
python geneva.py batch --input sample.csv --output results.csv
```

#### 4. Enterprise CLI (Multi-Agent System)
```bash
# Run audit evaluation
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Interactive chat query
python cli.py chat "Explain the scoring methodology"

# Verify audit trail integrity
python cli.py verify-audit

# Start REST API server
python cli.py serve --host 127.0.0.1 --port 8000
```

### Input Data Schema

| Field | Description | Type |
|:------|:------------|:-----|
| `Hypotension` | Blood pressure indicator | bool/int |
| `Tachycardia` | Heart rate indicator | bool/int |
| `Tachypnea` | Respiratory rate indicator | bool/int |
| `Fever` | Temperature indicator | bool/int |
| `Altered mental` | Mental status indicator | bool/int |

---

## 🌐 REST API

Start the server:
```bash
python cli.py serve
```

### Endpoints

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus-style metrics |
| POST | `/api/audit` | Submit task for evaluation |
| POST | `/api/chat` | Query supervisor chat |
| GET | `/api/audit/logs` | Get HMAC audit trail |

### Example API Request
```bash
curl -X POST http://localhost:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "TASK-001",
    "target_identifier": "KEY-001",
    "primary_metric": 28.5,
    "secondary_metric": 14.2,
    "status_descriptor": "NOMINAL",
    "is_critical_flag": false
  }'
```

---

## 🛡️ Security Features

### Zero-PHI Outbound Guard
- AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers
- Prevents accidental PHI leakage in audit logs and outputs

### HMAC-SHA256 Audit Trail
- Cryptographic, tamper-evident logging for every evaluation
- **Important:** Set `AUDIT_SECRET_KEY` environment variable in production for consistent key management
- If no key is set, a secure random key is generated per session (with warning)

### Running with Secure Configuration
```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
python cli.py serve
```

---

## 🧪 Testing

Run the full test suite:
```bash
pytest -v
```

Run with coverage:
```bash
pytest -v --cov=. --cov-report=term-missing
```

### Test Structure
- `test_geneva.py` — Core score calculation tests
- `tests/test_geneva_score_calculator.py` — Multi-agent system tests
- `tests/test_geneva_core.py` — Core module and security tests
- `tests/test_enrichment.py` — Enrichment feature tests

### Benchmark Simulation
```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
# Build and run with Docker
docker build -t geneva-score-calculator .
docker run -p 8000:8000 \
  -e AUDIT_SECRET_KEY=your-secure-key \
  geneva-score-calculator

# Or use Docker Compose
docker-compose up
```

---

## 📁 Project Structure

```
geneva-score-calculator/
├── geneva.py              # Core Geneva score calculation
├── cli.py                 # Enterprise CLI interface
├── enrichment.py          # Clinical enrichment features
├── simulator.py           # Benchmark simulation tool
├── sample.csv             # Sample patient data
├── Dockerfile             # Container build config
├── docker-compose.yml     # Multi-container orchestration
├── pyproject.toml         # Python package configuration
├── agents/
│   ├── __init__.py        # Package init
│   ├── base.py            # Security, PHI guard, audit trail
│   ├── models.py          # Pydantic data models
│   ├── supervisor.py      # Multi-agent orchestrator
│   ├── workers.py         # Specialized evaluation workers
│   ├── api.py             # FastAPI REST server
│   ├── llm_factory.py     # LLM provider abstraction
│   ├── learning.py        # Bayesian calibration engine
│   ├── metrics.py         # Prometheus metrics exporter
│   └── streamer.py        # WebSocket telemetry broadcaster
├── tests/
│   ├── test_geneva_core.py
│   ├── test_enrichment.py
│   └── test_geneva_score_calculator.py
└── web/
    └── index.html         # Operations dashboard UI
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
