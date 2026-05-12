# frozenenv

Typed environment variables as a frozen dataclass. Zero dependencies.

```bash
pip install frozenenv
```

## Install vs import

The PyPI package is `frozenenv` but the import name is `envclass`:

```bash
pip install frozenenv
```

```python
from envclass import envclass
```

## The problem

```python
# Old way — fragile, untyped, scattered
PORT = int(os.environ.get("PORT", "8000"))
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
```

## The envclass way

```python
from envclass import envclass

@envclass
class Config:
    DATABASE_URL: str          # required — raises EnvError if missing
    PORT: int = 8000           # optional, auto-cast to int
    DEBUG: bool = False        # "true"/"1"/"yes" → True
    ALLOWED_HOSTS: list[str] = []  # "a.com,b.com" → ["a.com","b.com"]

cfg = Config()        # reads os.environ + .env file automatically
print(cfg.PORT)       # 8000 — actual int, not "8000"
```

## Features

- **Zero dependencies** — pure Python stdlib
- **Type coercion** — `str`, `int`, `float`, `bool`, `list[X]`, `Optional[X]`
- **Frozen** — config is immutable after creation
- **Built-in .env support** — no python-dotenv needed
- **Fails fast** — clear error at startup, not buried in runtime

## Bool values accepted

| Truthy | Falsy |
|--------|-------|
| `true`, `1`, `yes`, `on`, `enabled` | `false`, `0`, `no`, `off`, `disabled` |

## Custom .env file path

```python
@envclass(env_file="/etc/myapp/.env.prod")
class Config:
    SECRET_KEY: str

# Or disable .env loading entirely:
@envclass(env_file=None)
class Config:
    SECRET_KEY: str
```

## Error handling

```python
from envclass import EnvError

try:
    cfg = Config()
except EnvError as e:
    print(f"Bad config: {e}")
    sys.exit(1)
```

## License

MIT — [github.com/hudihi/frozenenv](https://github.com/hudihi/frozenenv)