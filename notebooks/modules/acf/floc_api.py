from modules.util.api import ACFClient
from modules.util.helpers import Logger


class API_Floc:
    def __init__(self, config_id: str):
        self.api_client = ACFClient(config_id=config_id)
        self.endpoint = f"{self.api_client.base_url}/floc"
        self.log = Logger.get_logger(config_id)

    def get_flocs(self, batch_size: int = 100, filter: str = None):
        results = self.api_client.get_batches(
            endpoint=self.endpoint, batch_size=batch_size, filter=filter
        )
        self.log.info(f"[GET] Functional Locations: {len(results)}")
        return results
