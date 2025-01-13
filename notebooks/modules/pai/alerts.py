import requests
import backoff
from modules.util.api import APIClient
from modules.util.helpers import Logger


class AlertsAPIWrapper(APIClient):
    def __init__(self, config_id: str):
        super().__init__(config_id, "PAI")
        self.alerts_path = "/alerts/odata/v1"
        self.log = Logger.get_logger(config_id)

    @backoff.on_exception(
        backoff.expo,
        requests.exceptions.HTTPError,
        max_tries=5,
        giveup=lambda e: e.response.status_code not in [401],
    )
    def makeRequest(self, url, headers):
        response = requests.get(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return response

    def getAlerts(self, skip: int, top: int):
        """
        Fetches a chunk of alerts from the specified endpoint.

        This method constructs the full URL using the base URL and makes a GET request
        to retrieve the alerts. It includes the authorization token in the headers and
        handles the response.

        Returns:
            list: The list of alerts.

        Raises:
            requests.exceptions.HTTPError: If the request fails with a status code other than 200.
            ValueError: If the response body cannot be decoded as JSON.
        """
        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.base_url}{self.alerts_path}/Alerts?$format=json&$top={top}&$skip={skip}"

        # Debugging information
        print("URL info:", url)

        try:
            response = self.makeRequest(url, headers)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                self.log.warning("401 Unauthorized error, retrying...")
                self.token = None  # Invalidate the token to force refresh
                token = self.get_token()
                headers["Authorization"] = f"Bearer {token}"
                response = self.makeRequest(url, headers)
            else:
                raise

        data = response.json()

        if not data or not data.get("d", {}).get("results", []):
            self.log.info("No more data available, stopping.")
            return []

        return data.get("d", {}).get("results", [])

    def getCount(self):
        """
        Fetches the count of alerts from the specified endpoint.

        This method constructs the full URL using the base URL and makes a GET request
        to retrieve the count of alerts. It includes the authorization token in the headers
        and handles the response.

        Returns:
            int: The count of alerts.

        Raises:
            requests.exceptions.HTTPError: If the request fails with a status code other than 200.
        """

        @backoff.on_exception(
            backoff.expo,
            (requests.exceptions.HTTPError, requests.exceptions.RequestException),
            max_tries=5,
            giveup=lambda e: e.response.status_code not in [401],
        )
        def makeRequest(url, headers):
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response

        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.base_url}{self.alerts_path}/Alerts/$count"

        try:
            response = makeRequest(url, headers)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                self.log.warning("401 Unauthorized error, retrying...")
                self.token = None  # Invalidate the token to force refresh
                token = self.get_token()
                headers["Authorization"] = f"Bearer {token}"
                response = makeRequest(url, headers)
            else:
                raise

        count = int(response.text)

        return count

    def getAlertsById(self, alert_id: str):
        """
        Fetches a specific alert by its ID from the specified endpoint.

        This method constructs the full URL using the base URL and makes a GET request
        to retrieve the alert. It includes the authorization token in the headers and
        handles the response.

        Returns:
            dict: The alert details.

        Raises:
            requests.exceptions.HTTPError: If the request fails with a status code other than 200.
            ValueError: If the response body cannot be decoded as JSON.
        """
        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.base_url}{self.alerts_path}/Alerts('{alert_id}')?$format=json"

        # Debugging information
        self.log.info("URL info:", url)

        try:
            response = self.makeRequest(url, headers)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                self.log.warning("401 Unauthorized error, retrying...")
                self.token = None  # Invalidate the token to force refresh
                token = self.get_token()
                headers["Authorization"] = f"Bearer {token}"
                response = self.makeRequest(url, headers)
            else:
                raise

        data = response.json()

        if not data or not data.get("d"):
            self.log.info("No data available for the given alert ID.")
            return {}

        return data.get("d")
