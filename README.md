# IntentShield

IntentShield is a security-focused backend service for intent validation and policy enforcement.

## Requirements

- Python 3.11+
- pip

## Local Development

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Tests

```bash
pytest
```

## Docker

```bash
docker build -t intentshield .
docker run -p 8000:8000 intentshield
```

## License

MIT
