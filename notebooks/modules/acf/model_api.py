"""
MODEL API module for migration tooling
SAP API Documentation: https://api.sap.com/api/ModelAPI
"""

import requests
from modules.util.api import ACFClient, APIException
from modules.util.helpers import Logger


class ApiModel:
    def __init__(self, config_id: str):
        self.api_client = ACFClient(config_id=config_id)
        self.endpoint = f"{self.api_client.base_url}/models"
        self.log = Logger.get_logger(config_id=config_id)

    def get_model_model_id(self, id: str):
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
