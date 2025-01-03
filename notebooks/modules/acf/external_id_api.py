from modules.util.api import ACFClient
from modules.util.helpers import Logger


class ApiExternalId:
    def __init__(self, config_id: str):
        self.api_client = ACFClient(config_id=config_id)
        self.endpoint = self.api_client.base_url + "/externaldata"
        self.erp_ssid = self.api_client.erp_ssid
        self.log = Logger.get_logger(config_id)

    def get_external_data(self, filter: str, batch_size: int = 5000):
        results = self.api_client.get_batches(
            endpoint=self.endpoint, batch_size=batch_size, filter=filter
        )
        self.log.info(f"[GET] External Data {filter}: {len(results)}")
        return results
