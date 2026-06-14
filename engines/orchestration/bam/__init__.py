import importlib

_LAZY_MODULES: dict[str, str] = {
    "BamEngine": ".engine",
}


def __getattr__(name: str):
    if name in _LAZY_MODULES:
        mod = importlib.import_module(_LAZY_MODULES[name], __package__)
        val = getattr(mod, name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = sorted(_LAZY_MODULES.keys())
