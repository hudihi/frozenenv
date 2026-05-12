# tests file for envclass.py
import pytest
from envclass import envclass, EnvError


def test_reads_string(monkeypatch):
    monkeypatch.setenv("HOST", "localhost")

    @envclass(env_file=None)
    class Config:
        HOST: str

    assert Config().HOST == "localhost"
    
def test_reads_int(monkeypatch):
    monkeypatch.setenv("PORT", "9000")

    @envclass(env_file=None)
    class Config:
        PORT: int

    assert Config().PORT == 9000
    assert isinstance(Config().PORT, int)
    
def test_reads_float(monkeypatch):
    monkeypatch.setenv("RATE", "3.14")

    @envclass(env_file=None)
    class Config:
        RATE: float

    assert Config().RATE == 3.14
    

@pytest.mark.parametrize("val", ["true", "True", "1", "yes", "on", "enabled"])
def test_bool_true(monkeypatch, val):
    monkeypatch.setenv("FLAG", val)
    
    @envclass(env_file=None)
    class Config:
        FLAG: bool
        
    assert Config().FLAG is True
    

@pytest.mark.parametrize("val", ["false", "False", "0", "no", "off", "disabled"])
def test_bool_false(monkeypatch, val):
    monkeypatch.setenv("FLAG", val)
    
    @envclass(env_file=None)
    class Config:
        FLAG: bool
        
    assert Config().FLAG is False
    
def test_bool_invalid(monkeypatch):
    monkeypatch.setenv("FLAG", "notabool")
    
    @envclass(env_file=None)
    class Config:
        FLAG: bool
        
    with pytest.raises(EnvError, match="FLAG"):
        Config()
        
        
def test_list_of_strings(monkeypatch):
    monkeypatch.setenv("ITEMS", "apple,banana, cherry")

    @envclass(env_file=None)
    class Config:
        ITEMS: list[str]

    assert Config().ITEMS == ["apple", "banana", "cherry"]
    
def test_list_of_ints(monkeypatch):
    monkeypatch.setenv("PORTS", "8000, 9000, 10000")
    
    @envclass(env_file=None)
    class Config:
        PORTS: list[int]
        
    assert Config().PORTS == [8000, 9000, 10000]
    
def test_list_empty_string_gives_empty_list(monkeypatch):
    monkeypatch.setenv("ITEMS", "")
    
    @envclass(env_file=None)
    class Config:
        ITEMS: list[str]
        
    assert Config().ITEMS == []
    
    
def test_default_used_when_var_missing(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)

    @envclass(env_file=None)
    class Config:
        PORT: int = 8000

    assert Config().PORT == 8000
    
    

def test_env_overrides_default(monkeypatch):
    monkeypatch.setenv("PORT", "9000")
    
    @envclass(env_file=None)
    class Config:
        PORT: int = 8000
        
    assert Config().PORT == 9000
    
    
def test_missing_required_raises(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    @envclass(env_file=None)
    class Config:
        DATABASE_URL: str

    with pytest.raises(EnvError, match="DATABASE_URL"):
        Config()
        
def test_config_is_frozen(monkeypatch):
    monkeypatch.setenv("PORT", "8000")
    
    @envclass(env_file=None)
    class Config:
        PORT: int
        
    cfg = Config()
    with pytest.raises(Exception):   # FrozenInstanceError
        cfg.PORT = 9999              # type: ignore
        
        
def test_optional_present(monkeypatch):
    monkeypatch.setenv("TOKEN", "abc123")

    @envclass(env_file=None)
    class Config:
        TOKEN: str | None = None

    assert Config().TOKEN == "abc123"
    
    
def test_optional_missing_gives_none(monkeypatch):
    monkeypatch.delenv("TOKEN", raising=False)
    
    @envclass(env_file=None)
    class Config:
        TOKEN: str | None = None
    
    assert Config().TOKEN is None