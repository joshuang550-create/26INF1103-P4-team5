"""SmartBite automated test suite.

Run from the project root:
    python -m unittest discover -s tests -t . -v

No live AI connection, internet access or API key is needed: the AI is replaced by
a scripted fake model (tests/helpers.py) and Open Food Facts by a fake searcher.

The three third-party libraries that talk to the network (httpx, openfoodfacts,
google-genai) are only imported by the app, never called by the tests. If one of them
is not installed (for example when running outside Docker), a tiny stand-in module is
registered below so that the app's modules can still be imported. When the real
libraries are installed (as they are in the Docker image) nothing is replaced.
"""
import sys
import types


def _is_missing(module_name):
    try:
        __import__(module_name)
        return False
    except ImportError:
        return True


class _Anything:
    """Stand-in class that accepts any arguments."""
    def __init__(self, *args, **kwargs):
        pass


def _install_stand_ins():
    if _is_missing("httpx"):
        httpx = types.ModuleType("httpx")
        httpx.ConnectError = type("ConnectError", (Exception,), {})
        httpx.TimeoutException = type("TimeoutException", (Exception,), {})
        sys.modules["httpx"] = httpx

    if _is_missing("openfoodfacts"):
        off = types.ModuleType("openfoodfacts")
        off.API = _Anything
        sys.modules["openfoodfacts"] = off

    if _is_missing("google.genai"):
        google = sys.modules.get("google") or types.ModuleType("google")
        genai = types.ModuleType("google.genai")
        errors = types.ModuleType("google.genai.errors")
        types_mod = types.ModuleType("google.genai.types")

        class APIError(Exception):
            def __init__(self, code=None, *args):
                super().__init__(code)
                self.code = code

        errors.APIError = APIError
        for name in ("Content", "Part", "HttpRetryOptions", "HttpOptions", "GenerateContentConfig"):
            setattr(types_mod, name, _Anything)
        genai.Client = _Anything
        genai.errors = errors
        genai.types = types_mod
        google.genai = genai
        sys.modules.update({"google": google, "google.genai": genai,
                            "google.genai.errors": errors, "google.genai.types": types_mod})


_install_stand_ins()
