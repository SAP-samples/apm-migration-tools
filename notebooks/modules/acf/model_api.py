"""
MODEL API module for migration tooling
SAP API Documentation: https://api.sap.com/api/ModelAPI
"""

from modules.util.api import ACFClient
from modules.util.helpers import Logger


class ApiModel:
    def __init__(self, config_id: str):
        self.api_client = ACFClient(config_id=config_id)
        self.endpoint = f"{self.api_client.base_url}/models"
        self.log = Logger.get_logger(config_id=config_id)

    def get_model_model_id(self, id: str):

        api_url = f"{self.endpoint}({id})/header"
        res = self.api_client.get(endpoint=api_url)

        data = res.json()
        if data:
            return data

    def get_model_header(self, model_id: str):

        return self.get_model_model_id(id=model_id)

    def get_models(self):
        """
        Fetches the list of models from the specified endpoint.

        This method constructs the full URL using the base URL and makes a GET request
        to retrieve the models. It includes the authorization token in the headers and
        handles the response.

        Returns:
            dict: The JSON response containing the list of models.

        Raises:
            requests.exceptions.HTTPError: If the request fails with a status code other than 200.
        """

        # Make the request to the endpoint
        response = self.api_client.get(endpoint=self.endpoint)

        # Parse the JSON response
        data = response.json()

        return data

    def get_equipment_models(self) -> list:
        """
        Retrieve equipment models.

        This method fetches and returns models of type "EQU".

        Returns:
            list: A list of equipment models.
        """
        return self.get_models_by_type("EQU")

    def get_floc_models(self) -> list:
        return self.get_models_by_type("FLOC")

    def get_models_by_type(self, model_type: str) -> list:

        # Construct the full URL with filters, top, and skip parameters
        url = f"{self.endpoint}?$filter=modelType eq '{model_type}'"

        # Make the request to the endpoint
        response = self.api_client.get(endpoint=url)

        # Parse the JSON response
        data = response.json()

        # filter only models which have some value in the modelSearchTerms
        models = [model for model in data if model["modelSearchTerms"]]

        return models
