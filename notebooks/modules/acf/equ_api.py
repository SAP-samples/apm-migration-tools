# standard imports
from typing import Optional

# custom imports
from modules.util.api import ACFClient
from modules.util.helpers import Logger


class ApiEquipment:
    def __init__(self, config_id: str):
        self.api_client = ACFClient(config_id=config_id)
        self.endpoint = f"{self.api_client.base_url}/equipment"
        self.log = Logger.get_logger(config_id)

    def get_equipments(self, batch_size: int = 100, filter: Optional[str] = None):
        results = self.api_client.get_batches(
            endpoint=self.endpoint, batch_size=batch_size, filter=filter
        )
        self.log.info(f"[GET] Equipments: {len(results)}")
        return results
