from abc import ABC, abstractmethod
from typing import Dict, Optional


class BaseProcessor(ABC):
    name: str
    store: Dict[str, dict] = {}

    @abstractmethod
    def get_transaction(self, processor_txn_id: str) -> Optional[dict]:
        pass

    @abstractmethod
    def extract_raw_status(self, response: dict) -> str:
        pass

    @abstractmethod
    def normalize_status(self, response: dict) -> str:
        pass

    def add_to_store(self, processor_txn_id: str, data: dict):
        self.store[processor_txn_id] = data
