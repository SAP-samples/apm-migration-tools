import requests

from modules.base_class import BaseAPIWrapper
from modules.util.config import get_config_by_id, get_system_by_type


class TemplatedAPIWrapper(BaseAPIWrapper):
    def __init__(self, config_id: str):
        self.config = get_config_by_id(config_id)
        self.iot_config = get_system_by_type(self.config, "ACF")
        self.path = "/ain/services/api/v1"
        super().__init__(
            self.iot_config["credentials"]["client_id"],
            self.iot_config["credentials"]["client_secret"],
            self.iot_config["credentials"]["token_url"],
            self.iot_config["host"],
        )

    def get_template_by_type_code(self, type_code: str):

        headers = {"Authorization": f"Bearer {self._get_token()}"}
        # Construct the full URL with filters, top, and skip parameters
        url = f"{self.base_url}{self.path}/templates?$filter=typeCode eq '{type_code}'"

        # Make the request to the endpoint
        response = requests.get(url, headers=headers, timeout=self.timeout)

        # Raise an exception if the request failed
        if response.status_code != 200:
            response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        return data
