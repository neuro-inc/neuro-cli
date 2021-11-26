from yarl import URL

import neuro_sdk


def test_public_version() -> None:
    assert "__version__" in neuro_sdk.__all__


def test_module_for_public_names() -> None:
    for name in neuro_sdk.__all__:
        obj = getattr(neuro_sdk, name)
        if isinstance(obj, URL):
            # Default API url
            continue
        if hasattr(obj, "__module__"):
            assert obj.__module__ in (
                "neuro_sdk",
                # objects from typing are public type hint aliases,
                # e.g. Callable[...]
                "typing",
                # We re-export entities from admin client
                "neuro_admin_client.entities",
            ), f"{obj}.__module__ == {obj.__module__}, expected neuro_sdk"
