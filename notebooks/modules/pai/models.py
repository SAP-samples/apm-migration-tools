import requests

from modules.base_class import BaseAPIWrapper
from modules.util.config import get_config_by_id, get_system_by_type


class ModelAPIWrapper(BaseAPIWrapper):
    def __init__(self, config_id: str):
        self.config = get_config_by_id(config_id)
        self.acf_config = get_system_by_type(self.config, "ACF")
        self.path = "/ain/services/api/v1"
        super().__init__(
            self.acf_config["credentials"]["client_id"],
            self.acf_config["credentials"]["client_secret"],
            self.acf_config["credentials"]["token_url"],
            self.acf_config["host"],
        )

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

        headers = {"Authorization": f"Bearer {self._get_token()}"}
        # Construct the full URL with filters, top, and skip parameters
        url = f"{self.base_url}{self.path}/models"

        # Make the request to the endpoint
        response = requests.get(url, headers=headers, timeout=self.timeout)

        # Raise an exception if the request failed
        if response.status_code != 200:
            response.raise_for_status()

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
        headers = {"Authorization": f"Bearer {self._get_token()}"}
        # Construct the full URL with filters, top, and skip parameters
        url = f"{self.base_url}{self.path}/models?$filter=modelType eq '{model_type}'"

        # Make the request to the endpoint
        response = requests.get(url, headers=headers, timeout=self.timeout)

        # Raise an exception if the request failed
        if response.status_code != 200:
            response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        # filter only models which have some value in the modelSearchTerms
        models = [model for model in data if model["modelSearchTerms"]]

        return models
