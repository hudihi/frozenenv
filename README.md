# frozenenv

> Typed environment variables as a frozen dataclass — zero dependencies.

[![PyPI version](https://img.shields.io/pypi/v/frozenenv.svg)](https://pypi.org/project/frozenenv/)
[![Python versions](https://img.shields.io/pypi/pyversions/frozenenv.svg)](https://pypi.org/project/frozenenv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/hudihi/frozenenv/blob/main/LICENSE)
[![Zero dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)](https://pypi.org/project/frozenenv/)

---

## Install

```bash
pip install frozenenv
```

> **Note:** The PyPI package is `frozenenv` but the import name is `envclass`:
> ```python
> from envclass import envclass
> ```

---

## The problem

Every Python project that reads environment variables ends up with code like this:

```python
import os

# Fragile. Untyped. Scattered across the codebase.
DATABASE_URL = os.environ.get("DATABASE_URL")                        # str or None — no validation
PORT         = int(os.environ.get("PORT", "8000"))                   # crashes if PORT="abc"
DEBUG        = os.environ.get("DEBUG", "false").lower() == "true"    # hand-rolled bool parsing
HOSTS        = os.environ.get("ALLOWED_HOSTS", "").split(",")        # no types, no defaults
```

Problems with this approach:

- No central place listing all required env vars — you have to read all the code
- No type safety — `PORT` might silently stay a string
- Crashes deep at runtime, not at startup where it's easy to catch
- No IDE autocomplete on config values
- Every project hand-rolls the same boilerplate differently

---

## The frozenenv way

```python
from envclass import envclass

@envclass
class Config:
    DATABASE_URL: str              # required — raises EnvError if missing
    PORT: int = 8000               # optional, auto-cast to int
    DEBUG: bool = False            # "true" / "1" / "yes" → True
    ALLOWED_HOSTS: list[str] = []  # "a.com,b.com" → ["a.com", "b.com"]

cfg = Config()          # reads os.environ + .env file automatically

print(cfg.PORT)         # 8000   — actual int, not "8000"
print(cfg.DEBUG)        # False  — actual bool
print(cfg.ALLOWED_HOSTS)# ["a.com", "b.com"]

cfg.PORT = 9000         # ❌ FrozenInstanceError — config is immutable
```

Your config class is the single source of truth. Every required variable is visible at a glance, every type is enforced, and the app fails loudly at startup if something is missing — not buried in a runtime error 10 minutes later.

---

## Features

| Feature | frozenenv | python-dotenv | pydantic-settings |
|---|---|---|---|
| Type coercion | ✅ | ❌ | ✅ |
| Frozen / immutable | ✅ | ❌ | ❌ |
| Built-in .env parser | ✅ | ✅ | ✅ |
| Zero dependencies | ✅ | ✅ | ❌ |
| IDE autocomplete | ✅ | ❌ | ✅ |
| list[X] support | ✅ | ❌ | ✅ |
| Optional[X] support | ✅ | ❌ | ✅ |
| Decorator API | ✅ | ❌ | ❌ |

---

## Supported types

| Type | Example env value | Python value |
|---|---|---|
| `str` | `hello` | `"hello"` |
| `int` | `8000` | `8000` |
| `float` | `3.14` | `3.14` |
| `bool` | `true` / `1` / `yes` | `True` |
| `list[str]` | `a.com,b.com` | `["a.com", "b.com"]` |
| `list[int]` | `80,443,8080` | `[80, 443, 8080]` |
| `str \| None` | *(missing)* | `None` |
| `Optional[str]` | *(missing)* | `None` |

---

## Bool values

frozenenv accepts a wide range of truthy and falsy string values:

| Truthy | Falsy |
|---|---|
| `true`, `True`, `TRUE` | `false`, `False`, `FALSE` |
| `1` | `0` |
| `yes` | `no` |
| `on` | `off` |
| `enabled` | `disabled` |

Any other value raises an `EnvError` with a clear message.

---

## Usage examples

### Basic usage

```python
from envclass import envclass

@envclass
class Config:
    SECRET_KEY: str
    PORT: int = 8000
    DEBUG: bool = False

cfg = Config()
print(cfg.SECRET_KEY)
```

### Custom .env file path

```python
@envclass(env_file=".env.production")
class Config:
    DATABASE_URL: str
    SECRET_KEY: str
```

### Disable .env loading entirely

```python
@envclass(env_file=None)
class Config:
    DATABASE_URL: str   # reads from os.environ only
```

### .env file overrides real environment variables

```python
@envclass(override=True)
class Config:
    PORT: int = 8000    # .env value wins over os.environ
```

### Optional variables

```python
@envclass
class Config:
    DATABASE_URL: str
    SENTRY_DSN: str | None = None      # returns None if not set
    REDIS_URL: str | None = None
```

### List of typed values

```python
@envclass
class Config:
    ALLOWED_HOSTS: list[str] = []      # "a.com,b.com" → ["a.com","b.com"]
    ALLOWED_PORTS: list[int] = []      # "80,443" → [80, 443]
```

### Error handling

```python
import sys
from envclass import envclass, EnvError

@envclass
class Config:
    DATABASE_URL: str
    SECRET_KEY: str

try:
    cfg = Config()
except EnvError as e:
    print(f"Configuration error: {e}")
    sys.exit(1)
```

### Django example

```python
# settings.py
from envclass import envclass, EnvError

@envclass
class Env:
    SECRET_KEY: str
    DEBUG: bool = False
    DATABASE_URL: str
    ALLOWED_HOSTS: list[str] = ["localhost"]
    REDIS_URL: str | None = None

env = Env()

SECRET_KEY    = env.SECRET_KEY
DEBUG         = env.DEBUG
ALLOWED_HOSTS = env.ALLOWED_HOSTS
```

### FastAPI example

```python
# config.py
from functools import lru_cache
from envclass import envclass

@envclass
class Settings:
    APP_NAME: str = "My API"
    DATABASE_URL: str
    SECRET_KEY: str
    DEBUG: bool = False

@lru_cache
def get_settings():
    return Settings()
```

```python
# main.py
from fastapi import Depends
from config import Settings, get_settings

@app.get("/info")
def info(settings: Settings = Depends(get_settings)):
    return {"app": settings.APP_NAME}
```

---

## .env file format

frozenenv parses `.env` files with no external dependency. Supported syntax:

```bash
# Comments are ignored
DATABASE_URL=postgres://localhost/mydb

# Quoted values
SECRET_KEY="my secret key with spaces"
APP_NAME='My Application'

# export keyword is supported
export PORT=8000

# Comma-separated lists
ALLOWED_HOSTS=localhost,127.0.0.1,myapp.com
ALLOWED_PORTS=80,443

# Optional values (empty = None for Optional types)
SENTRY_DSN=
```

---

## API reference

### `@envclass`

Decorator that converts a class into a typed, frozen environment config object.

```python
@envclass(
    env_file: str | None = ".env",   # path to .env file, None to disable
    override: bool = False,          # if True, .env values override os.environ
)
```

**Parameters:**

- `env_file` — Path to a `.env` file. Defaults to `.env` in the current working directory. Set to `None` to skip file loading entirely.
- `override` — If `True`, values from the `.env` file take precedence over real environment variables. Default is `False` (real env wins).

**Behaviour:**

- All annotated fields without defaults are **required** — missing ones raise `EnvError` immediately
- Fields with defaults are **optional** — the default is used when the variable is not set
- The resulting object is **frozen** — attempting to set any attribute raises `FrozenInstanceError`
- Full IDE autocomplete because the result is a real Python dataclass

---

### `EnvError`

Raised when a required variable is missing or a value cannot be cast to the declared type.

```python
from envclass import EnvError

try:
    cfg = Config()
except EnvError as e:
    # e.g: "Missing required environment variable(s): DATABASE_URL, SECRET_KEY"
    # e.g: "PORT: cannot cast 'abc' to int"
    # e.g: "DEBUG: 'maybe' is not a valid bool. Use: 0, 1, disabled, enabled, ..."
    print(e)
```

---

## Requirements

- Python 3.10 or higher
- Zero external dependencies — pure Python stdlib only

---

## Contributing

Contributions are welcome. To get started:

```bash
git clone https://github.com/hudihi/frozenenv.git
cd frozenenv
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest tests/ -v
```

Please open an issue before submitting a pull request for large changes.

---

## Changelog

### 0.1.0 — 2026-05-12
- Initial release
- Type coercion: `str`, `int`, `float`, `bool`, `list[X]`, `Optional[X]`
- Built-in `.env` file parser — no python-dotenv needed
- Frozen / immutable config objects
- `override` mode for `.env` priority
- Clear `EnvError` messages for missing and invalid variables

---

## License

MIT — [github.com/hudihi/frozenenv](https://github.com/hudihi/frozenenv)
