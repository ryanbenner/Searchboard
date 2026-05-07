from typing import Type
from jobscraper.sources.base import Source

REGISTRY: dict[str, Type[Source]] = {}


def register(name: str):
    def deco(cls):
        cls.name = name
        REGISTRY[name] = cls
        return cls
    return deco
