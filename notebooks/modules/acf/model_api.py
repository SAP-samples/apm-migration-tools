"""
MODEL API module for migration tooling
SAP API Documentation: https://api.sap.com/api/ModelAPI
"""

# standard imports
import requests

# custom imports
from modules.util.api import ACFClient, APIException
from modules.util.helpers import Logger


class ApiModel:

    """
    ApiModel is a class that provides methods to interact with the ACF API for model-related operations.
    Attributes:
        api_client (ACFClient): An instance of the ACFClient to handle API requests.
        endpoint (str): The base URL endpoint for model-related API calls.
        log (Logger): A logger instance for logging purposes.
    Methods:
        __init__(config_id: str):
            Initializes the ApiModel with the given configuration ID.
        get_model_model_id(id: str):
            Retrieves the model header information for the given model ID.
    """

    def __init__(self, config_id: str):

        """
        Initializes the model API with the given configuration ID.
        Args:
            config_id (str): The configuration ID used to initialize the ACFClient.
        Attributes:
            api_client (ACFClient): The client used to interact with the ACF API.
            endpoint (str): The endpoint URL for the models.
            log (Logger): The logger instance for logging purposes.
        """

        self.api_client = ACFClient(config_id=config_id)
        self.endpoint = f"{self.api_client.base_url}/models"
        self.log = Logger.get_logger(config_id=config_id)

    def get_model_model_id(self, id: str):

        """
        Retrieve model details by model ID.
        Args:
            id (str): The ID of the model to retrieve.
        Returns:
            dict: The JSON response containing model details if the request is successful.
        Raises:
            APIException: If the request to the API endpoint fails with a status code other than 200.
        """

        headers = {
            "Authorization": f"Bearer {self.api_client.get_token()}",
            "Content-Type": "application/json",
        }

        api_url = f"{self.endpoint}({id})/header"
        res = requests.get(api_url, headers=headers, timeout=self.api_client.timeout)

        if res.status_code != 200:
            raise APIException(
                endpoint=api_url, status_code=res.status_code, response=res.text
            )

        data = res.json()
        if data:
            return data
