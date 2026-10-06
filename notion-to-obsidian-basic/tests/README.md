# Running tests

The skill scripts have no external dependencies (stdlib only). `pytest` is the only external lib, used only here.

```bash
# From the skill root:
uv run --with pytest pytest tests/ -v
```

No venv setup needed — `uv` fetches pytest on demand.
