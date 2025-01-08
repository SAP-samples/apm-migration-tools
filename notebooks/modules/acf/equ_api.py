"""
Equipment API module for migration tooling
SAP API Documentation: https://api.sap.com/api/EquipmentAPI
"""

# standard imports
from typing import Optional

# custom imports
from modules.util.api import ACFClient
from modules.util.helpers import Logger


class ApiEquipment:

    """
    A class to interact with the equipment API.
    Attributes:
    api_client : ACFClient
        An instance of the ACFClient to make API requests.
    endpoint : str
        The endpoint URL for the equipment API.
    log : Logger
        A logger instance for logging information.
    Methods:
    __init__(config_id: str)
        Initializes the ApiEquipment with a given configuration ID.
    get_equipments(batch_size: int = 100, filter: Optional[str] = None)
        Retrieves equipment data in batches from the API.
    """

    def __init__(self, config_id: str):

        """
        Initializes the EquApi class with the given configuration ID.
        Args:
            config_id (str): The configuration ID used to initialize the ACFClient.
        Attributes:
            api_client (ACFClient): An instance of ACFClient initialized with the given config_id.
            endpoint (str): The endpoint URL for the equipment API.
            log (Logger): A logger instance for logging purposes.
        """

        self.api_client = ACFClient(config_id=config_id)
        self.endpoint = f"{self.api_client.base_url}/equipment"
        self.log = Logger.get_logger(config_id)

    def get_equipments(self, batch_size: int = 100, filter: Optional[str] = None):

        """
        Retrieve a batch of equipment data from the API.
        Args:
            batch_size (int, optional): The number of equipment records to retrieve in each batch. Defaults to 100.
            filter (Optional[str], optional): An optional filter string to apply to the equipment data retrieval. Defaults to None.
        Returns:
            List[Dict]: A list of dictionaries containing the equipment data.
        Logs:
            Logs the number of equipment records retrieved.
        """

        results = self.api_client.get_batches(
            endpoint=self.endpoint, batch_size=batch_size, filter=filter
        )
        self.log.info(f"[GET] Equipments: {len(results)}")
        return results
