"""
Functional Location API module for migration tooling
SAP API Documentation: https://api.sap.com/api/FunctionalLocationAPI
"""

# custom imports
from modules.util.api import ACFClient
from modules.util.helpers import Logger


class ApiFloc:

    """
    ApiFloc is a class that provides methods to interact with the Functional Locations (FLOC) API.
    Attributes:
        api_client (ACFClient): An instance of the ACFClient initialized with the provided config_id.
        endpoint (str): The endpoint URL for the FLOC API.
        log (Logger): A logger instance for logging information and errors.
    Methods:
        __init__(config_id: str):
            Initializes the ApiFloc instance with the given configuration ID.
        get_flocs(batch_size: int = 100, filter: str = None):
            Retrieves functional locations in batches from the FLOC API.
            Args:
                batch_size (int): The number of records to retrieve per batch. Default is 100.
                filter (str): An optional filter string to apply to the API request.
            Returns:
                list: A list of functional locations retrieved from the API.
    """

    def __init__(self, config_id: str):

        """
        Initializes the FlocApi instance with the given configuration ID.
        Args:
            config_id (str): The configuration ID used to initialize the ACFClient and logger.
        Attributes:
            api_client (ACFClient): The client used to interact with the ACF API.
            endpoint (str): The endpoint URL for the floc API.
            log (Logger): The logger instance for logging messages.
        """

        self.api_client = ACFClient(config_id=config_id)
        self.endpoint = f"{self.api_client.base_url}/floc"
        self.log = Logger.get_logger(config_id)

    def get_flocs(self, batch_size: int = 100, filter: str = None):

        """
        Retrieve functional locations in batches.
        Args:
            batch_size (int, optional): The number of functional locations to retrieve per batch. Defaults to 100.
            filter (str, optional): A filter string to apply to the retrieval. Defaults to None.
        Returns:
            list: A list of functional locations retrieved from the API.
        """

        results = self.api_client.get_batches(
            endpoint=self.endpoint, batch_size=batch_size, filter=filter
        )
        self.log.info(f"[GET] Functional Locations: {len(results)}")
        return results
