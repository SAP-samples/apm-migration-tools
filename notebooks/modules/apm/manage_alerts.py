import requests
from modules.util.api import APIClient
from modules.util.config import get_config_by_id, get_system_by_type
from modules.util.helpers import Logger


class APMAlertAPIWrapper(APIClient):
    def __init__(self, config_id: str):
        super().__init__(config_id, "APM")
        self.alerts_path = "/AlertsService/v1"
        self.alerttpye_path = "/AlertTypeService/v1"
        self.log = Logger.get_logger(config_id)

    def getApmAlerts(self):
        """
        Fetches the list of alerts from the specified endpoint.

        This method constructs the full URL using the base URL and makes a GET request
        to retrieve the alerts. It includes the authorization token in the headers and
        handles the response.

        Returns:
            dict: The JSON response containing the list of alerts.

        Raises:
            requests.exceptions.HTTPError: If the request fails with a status code other than 200.
        """
        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}", "x-api-key": self.x_api_key}
        url = f"{self.base_url}{self.alerts_path}/Alert?$expand=TechnicalObject($select=Name,Number,Type)"

        response = requests.get(url, headers=headers, timeout=self.timeout)

        if response.status_code != 200:
            response.raise_for_status()

        data = response.json()

        return data

    def getApmAlerttypes(self):
        """
        Fetches the list of alert types from the specified endpoint.

        This method constructs the full URL using the base URL and makes a GET request
        to retrieve the alert types. It includes the authorization token in the headers
        and handles the response.

        Returns:
            dict: The JSON response containing the list of alert types.

        Raises:
            requests.exceptions.HTTPError: If the request fails with a status code other than 200.
        """
        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}", "x-api-key": self.x_api_key}
        url = f"{self.base_url}{self.alerttpye_path}/AlertType"

        response = requests.get(url, headers=headers, timeout=self.timeout)

        if response.status_code != 200:
            response.raise_for_status()

        data = response.json()

        return data

    def getApmAlertCount(self):
        """
        Fetches the count of alerts from the specified endpoint.

        This method constructs the full URL using the base URL and makes a GET request
        to retrieve the count of alerts. It includes the authorization token and API key
        in the headers and handles the response.

        Returns:
            int: The count of alerts.

        Raises:
            requests.exceptions.HTTPError: If the request fails with a code other than 200.
        """

        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}", "x-api-key": self.x_api_key}
        url = f"{self.base_url}{self.alerts_path}/Alert/$count"

        response = requests.get(url, headers=headers, timeout=self.timeout)

        if response.status_code != 200:
            response.raise_for_status()

        count = int(response.text)
        return count

    def getApmAlerttypeCount(self):
        """
        Fetches the count of alert types from the specified endpoint.

        This method constructs the full URL using the base URL and makes a GET request
        to retrieve the count of alert types. It includes the authorization token and API key
        in the headers and handles the response.

        Returns:
            int: The count of alert types.

        Raises:
            requests.exceptions.HTTPError: If the request fails with a code other than 200.
        """
        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}", "x-api-key": self.x_api_key}
        url = f"{self.base_url}{self.alerttpye_path}/AlertType/$count"

        response = requests.get(url, headers=headers, timeout=self.timeout)

        if response.status_code != 200:
            response.raise_for_status()

        count = int(response.text)
        return count

    def postAlert(self, alert_type: str, triggered_on: str, technical_objects: list):
        """
        Posts a new alert to the specified endpoint.

        This method constructs the full URL using the base URL and makes a POST request
        to create a new alert. It includes the authorization token and API key in the headers
        and sends the alert data in the body.

        Args:
            alert_type (str): The type of the alert.
            triggered_on (str): The timestamp when the alert was triggered.
            technical_objects (list): A list of technical objects associated with the alert.

        Returns:
            dict: The JSON response from the server or a message indicating the alert type does not have origin as API.

        Raises:
            requests.exceptions.HTTPError: If the request fails with a status code other than 201.
        """
        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}", "x-api-key": self.x_api_key}
        url = f"{self.base_url}{self.alerts_path}/Alert"

        body = {
            "AlertType": alert_type,
            "TriggeredOn": triggered_on,
            "TechnicalObject": technical_objects,
        }

        response = requests.post(url, headers=headers, json=body, timeout=self.timeout)

        if response.status_code != 201:
            response.raise_for_status()

        data = response.json()
        return data

    def postAlerttype(
        self,
        name: str,
        category: str,
        source: str,
        description: str,
        default_severity: str,
        default_severity_description: str,
        deduplication_period: str = None,
        deduplication_is_enabled: bool = None,
    ):
        """
        Posts a new alert type to the specified endpoint.

        This method constructs the full URL using the base URL and makes a POST request
        to create a new alert type. It includes the authorization token and API key in the headers
        and sends the alert type data in the body.

        Args:
            name (str): The name of the alert type.
            category (str): The category of the alert type.
            source (str): The source of the alert type
            description (str): The description of the alert type.
            default_severity (int): The default severity of the alert type.
            default_severity_description (str): The description of the default severity.
            deduplication_period (str, optional): The deduplication period. Defaults to None.
            deduplication_is_enabled (bool, optional): Whether deduplication is enabled. Defaults to None.

        Returns:
            dict: The JSON response from the server or a message indicating the alert type already exists.

        Raises:
            requests.exceptions.HTTPError: If the request fails with a status code other than 201.
        """
        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}", "x-api-key": self.x_api_key}
        url = f"{self.base_url}{self.alerttpye_path}/AlertType"

        body = {
            "Name": name,
            "Category": category,
            "Source": source,
            "Description": description,
            "DefaultSeverity": default_severity,
            "DefaultSeverityDescription": default_severity_description,
            "DeduplicationPeriod": deduplication_period,
            "DeduplicationIsEnabled": deduplication_is_enabled,
        }

        response = requests.post(url, headers=headers, json=body, timeout=self.timeout)

        if response.status_code != 201:
            response.raise_for_status()

        data = response.json()
        return data
