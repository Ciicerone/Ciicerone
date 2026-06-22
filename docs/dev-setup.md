## Development Setup

### Prerequisites
- Python >= 3.11
- pip >= 23
- virtualenv

### Recommended Setup
```bash
git clone https://github.com/Ciicerone/Ciicerone
cd Ciicerone
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt
pytest
ciicerone status

## Optional: Quick setup using Makefile

If you have Python 3.11 installed:

```bash
make dev
