import requests
import backoff
from modules.util.api import APIClient, APIException
from modules.util.helpers import Logger


class AlertTypeAPIWrapper(APIClient):
    def __init__(self, config_id: str):
        super().__init__(config_id, "ACF")
        self.alerttype_path = "/ain/services/api/v1"
        self.log = Logger.get_logger(config_id)

    @backoff.on_exception(
        backoff.expo,
        requests.exceptions.HTTPError,
        max_tries=5,
        giveup=lambda e: e.response.status_code not in [401, 500],
    )
    def makeRequest(self, url, headers):
        response = requests.get(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return response

    def getAlerttypes(self):
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
        url = f"{self.base_url}{self.alerttype_path}/alerttypes"

        try:
            response = self.makeRequest(url, headers)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                self.log.warning("401 Unauthorized error, retrying...")
                self.token = None  # Invalidate the token to force refresh
                token = self.get_token()
                headers["Authorization"] = f"Bearer {token}"
                response = self.make_request(url, headers)
            else:
                raise

        data = response.json()

        return data
