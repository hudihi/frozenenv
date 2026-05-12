from __future__ import annotations

import dataclasses
import os
import pathlib
import types
import typing
from typing import Any, get_type_hints

__all__ = ["envclass", "EnvError"]
__version__ = "0.1.0"

__BOOL_TRUE = {"1", "true", "yes", "on", "enabled"}
__BOOL_FALSE = {"0", "false", "no", "off", "disabled"}



class EnvError(Exception):
    """Raised when a required env var is missing or cannot be cast to the expected type."""
    
    
def _parse_dotenv(path: str | os.PathLike) -> dict[str, str]:
    """Parse KEY=VALUE lines from a .env file. Returns empty dict if not found."""
    result: dict[str, str] = {}
    p = pathlib.Path(path)
    
    if not p.exists():
        return result
    
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        
        #strip surrounding quotes if present
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        if key:
            result[key] = value
    return result


def _coerce(value: str, annotation: Any, name: str) -> Any:
    """Cast string value to the given type annontation."""
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)


    # Optional[X] or X | None
    if origin is typing.Union or origin is types.UnionType:
        non_none = [a for a in args if a is not type(None)]
        if not value and type(None) in args:
            return None
        return _coerce(value, non_none[0], name) if non_none else value

    # bool - must come before int (bool is a subclass of int!)
    if annotation is bool:
        val = value.lower()
        if val in __BOOL_TRUE:
            return True
        if val in __BOOL_FALSE:
            return False
        opts = ", ".join(sorted(__BOOL_TRUE | __BOOL_FALSE))
        raise EnvError(f"{name}: '{value}' is not a valid bool. Use: {opts}")

    # int, float, str
    if annotation in (int, float, str):
        try:
            return annotation(value)
        except (ValueError, TypeError) as exc:
            raise EnvError(f"{name}: cannot cast '{value} to {annotation.__name__} ") from exc
    # list[X] - comma-separated
    if origin is list:
        if not value:
            return []
        item_type = args[0] if args else str
        return [_coerce(v.strip(), item_type, name) for v in value.split(",")]
        
    # Fallback: return as string
    return value

def envclass(cls=None, *, env_file: str | os.PathLike | None = ".env",override: bool = False):
    """Decorator that turns a class into a typed, frozen env-var config object.
    
    Args:
    env_file: Path to a .env file to load. Defaults to '.env' in cwd.
              Set to None to skip .env loading entirely.
    override: If True, .env values overwrite real environment variables.
    """
    
    def wrap(klass):
        # 1. Make it a frozen dataclass so config can't be mutated
        dc = dataclasses.dataclass(klass, frozen=True)
        
        
        # 2. Grab the resolved type hints (handles forward refs)
        hints = get_type_hints(dc)
        
        # 3. Collect defaults from the dataclass fields
        defaults: dict[str, Any] = {}
        for f in dataclasses.fields(dc):
            if f.default is not dataclasses.MISSING:
                defaults[f.name] = f.default
            elif f.default_factory is not dataclasses.MISSING:
                defaults[f.name] = f.default_factory()
            
        # 4. Build a custom __init__ that reads from env
        original_init = dc.__init__
        
        def __init__(self, *, _env: dict[str, str] | None = None):
            # Load .env file first
            dotenv_vals: dict[str, str] = {}
            
            if env_file is not None:
                dotenv_vals = _parse_dotenv(env_file)
                
            # Merge: real env wins unless override=True
            source = dict(dotenv_vals)
            if override:
                source.update(os.environ)
            else:
                for k, v in os.environ.items():
                    source[k] = v
                    
            # Allow test injection via _env parameter
            if _env is not None:
                source.update(_env)
                
            # Resolve each field
            kwargs: dict[str, Any] = {}
            missing = []
            
            for field_name, annotation in hints.items():
                raw = source.get(field_name)
                if raw is not None:
                    kwargs[field_name] = _coerce(raw, annotation, field_name)
                elif field_name in defaults:
                    kwargs[field_name] = defaults[field_name]
                else:
                    missing.append(field_name)
                    
            if missing:
                raise EnvError(f"Missing required env vars: {', '.join(missing)}")
        
            # Call the frozen dataclass __init__ via object.__setattr__
            for k, v in kwargs.items():
                object.__setattr__(self, k, v)
        
        dc.__init__ = __init__
        return dc
    
    if cls is None:
        return wrap
    return wrap(cls)
    
    