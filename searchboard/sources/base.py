from abc import ABC, abstractmethod
from searchboard.job import Job


class Source(ABC):
    name: str = ""

    @abstractmethod
    def fetch(self) -> list[Job]:
        """Return all currently-listed jobs from this source."""
