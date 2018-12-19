from pkg_resources import get_distribution

from .client import Model, Storage, Resources, JobItem

__version__ = get_distribution(__name__).version

__all__ = ["__version__", "Model", "Storage", "Resources", "JobItem"]
