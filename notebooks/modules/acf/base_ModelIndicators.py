import requests
from modules.util.api import ACFClient, APIException
import backoff
import time


class BaseModelIndicators:
    def __init__(self, config_id: str, endpoint_suffix: str):
        """
        Initializes the class object with necessary variables and utility module objects
        """
        self.api_client = ACFClient(config_id=config_id)
        self.endpoint = f"{self.api_client.base_url}/{endpoint_suffix}"

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.RequestException, APIException),
        max_time=300,
        giveup=lambda e: e.response is not None and e.response.status_code == 429,
        max_tries=5,
    )
    def get_model_indicator(self, guid: str):
        """
        Fetches the model indicator for a given GUID.
        This method sends a GET request to the API endpoint to retrieve the model templates
        associated with the specified GUID. It uses the authorization token from
        the API client for authentication.
        Args:
            guid (str): The GUID for which the model indicator is to be fetched.
        Returns:
            dict: A dictionary containing the JSON response from the API, which includes the model templates.
        Raises:
            APIException: If the API request fails (i.e., the status code is not 200), an APIException is raised
                            with details about the endpoint, status code, and response text.
        """

        headers = {
            "Authorization": f"Bearer {self.api_client.get_token()}",
            "Content-Type": "application/json",
        }

        api_url = f"{self.endpoint}({guid})/model/templates"
        res = requests.get(url=api_url, headers=headers)

        if res.status_code == 429:
            retry_attempt = res.headers.get("Retry-After", "unknown")
            print(f"Rate limit exceeded. Retry after {retry_attempt} seconds.")
            time.sleep(30)
        elif res.status_code != 200:
            raise APIException(
                endpoint=api_url,
                status_code=res.status_code,
                response="No Content" if res.status_code == 204 else res.text,
            )
        return res.json()
