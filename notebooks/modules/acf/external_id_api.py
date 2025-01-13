"""
External IDs API module for migration tooling
SAP API Documentation: https://api.sap.com/api/ExternalIDsAPI
"""

# custom imports
from modules.util.api import ACFClient
from modules.util.helpers import Logger


class ApiExternalId:

    """
    A class to interact with the external ID API.
    Attributes:
        api_client (ACFClient): The API client used to make requests.
        endpoint (str): The endpoint URL for external data.
        erp_ssid (str): The ERP session ID.
        log (Logger): The logger instance for logging information.
    Methods:
        get_external_data(filter: str, batch_size: int = 5000):
            Retrieves external data based on the provided filter and batch size.
    """

    def __init__(self, config_id: str):

        """
        Initializes the ApiExternalId instance with the given configuration ID.
        Args:
            config_id (str): The configuration ID used to initialize the API client.
        """

        self.api_client = ACFClient(config_id=config_id)
        self.endpoint = self.api_client.base_url + "/externaldata"
        self.erp_ssid = self.api_client.erp_ssid
        self.log = Logger.get_logger(config_id)

    def get_external_data(self, filter_str: str, batch_size: int = 5000):

        """
        Retrieves external data based on the provided filter and batch size.
        Args:
            filter (str): The filter criteria for retrieving external data.
            batch_size (int, optional): The number of records to retrieve in each batch. Defaults to 5000.
        Returns:
            list: A list of results retrieved from the external data API.
        """

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
