# standard imports
import requests

# custom imports
from modules.util.api import APMClient, APIException
from modules.util.helpers import Logger

"""
SAP API Documentation: https://api.sap.com/api/TechnicalObjects_APIs/path/get_TechnicalObjects
"""


class ApiTechnicalObjects:
    """
    A class to interact with the Technical Object Service API.
    """

    def __init__(self, config_id: str):

        """
        Initializes the class object with necessary variables and utility module objects
        """

        self.api_client = APMClient(
            config_id=config_id, service="TechnicalObjectService"
        )
        self.endpoint = f"{self.api_client.base_url}"
        self.log = Logger.get_logger(config_id)

    def get_technical_object_number(self, external_id: str) -> dict:

        """
        Get the technical object number (internal ID) maintained in APM for a given external ID
        """

        headers = {
            "Authorization": f"Bearer {self.api_client.get_token()}",
            "Content-Type": "application/json",
            "x-api-key": self.api_client.x_api_key,
        }

        endpoint_suffix = "/TechnicalObjects"

        api_url = f"{self.api_client.base_url}{endpoint_suffix}"

        params = {
            "$filter": f"technicalObject eq '{external_id}' and SSID eq '{self.api_client.erp_ssid}'",
            "$select": "number,technicalObject",
        }

        res = requests.get(
            url=api_url, timeout=self.api_client.timeout, headers=headers, params=params
        )

        if res.status_code != 200:
            raise APIException(
                endpoint=api_url, status_code=res.status_code, response=res.text
            )

        data = res.json()
        response = data.get("value", [])[0]
        return response
