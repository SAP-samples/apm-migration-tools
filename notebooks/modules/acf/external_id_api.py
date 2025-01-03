from modules.util.api import ACFClient
from modules.util.helpers import Logger


class ApiExternalId:
    def __init__(self, config_id: str):
        self.api_client = ACFClient(config_id=config_id)
        self.endpoint = self.api_client.base_url + "/externaldata"
        self.erp_ssid = self.api_client.erp_ssid
        self.log = Logger.get_logger(config_id)

    def get_external_data(self, filter_str: str, batch_size: int = 5000):
        results = self.api_client.get_batches(
            endpoint=self.endpoint, batch_size=batch_size, filter=filter_str
        )
        self.log.info("[GET] External Data %s: %d", filter_str, len(results))
        return results

    def get_acf_object_by_thing_id(self, external_id: str):
        url = f"{self.api_client.base_url}/objectsid/ainobjects({external_id})?$filter=systemName eq 'pdmsSysThing'"
        results = self.api_client.get(url)
        if results:
            self.log.info("[GET] ACF Object by External ID %s", external_id)
            return results.json()[0]
        else:
            self.log.error("[GET] ACF Object by External ID %s: Not Found", external_id)
            return None

    def get_acf_model_id_by_thing_type(self, thing_type: str):
        url = f"{self.api_client.base_url}/objectsid/ainobjects({thing_type})?$filter=systemName eq 'pdmsSysPackage'"
        results = self.api_client.get(url)
        if results:
            self.log.info("[GET] ACF Model Id by External ID %s", thing_type)
            return results.json()[0]
        else:
            self.log.error(
                "[GET] ACF Model Id by External ID %s: Not Found", thing_type
            )
            return None
