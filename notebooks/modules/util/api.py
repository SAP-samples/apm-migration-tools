"""Utility module for APIs"""

import requests
import time
import base64
from modules.util.config import get_config_by_id, get_system_by_type


class BaseAPIClient:
    def __init__(
        self, client_id, client_secret, token_url, base_url, x_api_key: str = None
    ):
        """
        Initialize the API client with the given credentials and configuration.

        Args:
            client_id (str): The client ID for authentication.
            client_secret (str): The client secret for authentication.
            token_url (str): The URL to obtain the authentication token.
            base_url (str): The base URL for the API endpoints.
            x_api_key (str, optional): An optional API key for additional authentication. Defaults to None.

        Attributes:
            client_id (str): The client ID for authentication.
            client_secret (str): The client secret for authentication.
            token_url (str): The URL to obtain the authentication token.
            base_url (str): The base URL for the API endpoints.
            x_api_key (str, optional): An optional API key for additional authentication.
            timeout (int): The timeout duration for API requests, in seconds. Defaults to 30.
            token (str, optional): The authentication token. Defaults to None.
            token_expiry (int): The expiry time of the authentication token. Defaults to 0.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.base_url = base_url
        self.x_api_key = x_api_key
        self.timeout = 30
        self.token = None
        self.token_expiry = 0
        self.timeout = 30

    def get_token(self):
        """
        Retrieves an authentication token. If the current token is expired or not set,
        it authenticates using client credentials and fetches a new token from the token URL.
        Returns:
            str: The authentication token.
        Raises:
            requests.exceptions.RequestException: If the request to the token URL fails.
        """
        if self.token_expiry == None or time.time() >= self.token_expiry:
            # Authenticate and get the token
            response = requests.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            response_data = response.json()
            self.token = response_data.get("access_token")

            expires_in = response_data.get("expires_in")
            self.token_expiry = time.time() + expires_in
        return self.token


class APIClient(BaseAPIClient):
    def __init__(self, config_id: str, system_type: str):
        self.config = get_config_by_id(config_id)
        self.sys_config = get_system_by_type(self.config, system_type)
        super().__init__(
            base_url=self.sys_config["host"],
            client_id=self.sys_config["credentials"]["client_id"],
            client_secret=self.sys_config["credentials"]["client_secret"],
            token_url=self.sys_config["credentials"]["token_url"],
            x_api_key=self.sys_config.get("credentials", {}).get("x_api_key"),
        )

    def get_batches(
        self,
        endpoint: str,
        batch_size: int = 100,
        filter: str = None,
        expand: str = None,
    ):

        headers = {
            "Authorization": f"Bearer {super().get_token()}",
            "Content-Type": "application/json",
        }

        if self.x_api_key:
            headers["x-api-key"] = self.x_api_key

        response = []
        top = batch_size
        skip = 0

        while True:
            api_url = endpoint
            params = {}

            if filter:
                params["$filter"] = filter

            if top:
                params["$top"] = top

            if skip:
                params["$skip"] = skip

            if expand:
                params["$expand"] = expand

            try:
                res = requests.get(url=api_url, headers=headers, params=params)
                if res.status_code != 200:
                    raise APIException(
                        endpoint=api_url, status_code=res.status_code, response=res.text
                    )
                data = res.json()
                if not data:
                    break

                count = 0

                if isinstance(data, dict) and "value" in data:
                    response.extend(data["value"])
                    count = len(data["value"])
                else:
                    response.extend(data)
                    count = len(data)

                if count < top:
                    break
                skip += top
            except Exception as e:
                raise Exception(f"API call failed: {e}")
        return response


class ACFClient(APIClient):
    def __init__(self, config_id: str):
        super().__init__(config_id, "ACF")
        self.base_url = f"{self.base_url}/ain/services/api/v1"

        self.erp_config = get_system_by_type(self.config, "ERP")
        self.erp_ssid = (
            f"{str(self.erp_config['sys_id']).upper()}_{self.erp_config['client']}"
        )


class APMClient(APIClient):
    def __init__(self, config_id: str, service: str):
        super().__init__(config_id, "APM")
        self.base_url = f"{self.base_url}/{service}/v1"

        self.erp_config = get_system_by_type(self.config, "ERP")
        self.erp_ssid = (
            f"{str(self.erp_config['sys_id']).upper()}_{self.erp_config['client']}"
        )


class ERPClient:
    def __init__(self, config_id: str, service: str, entity_set: str):

        self.config = get_config_by_id(config_id)
        self.sys_config = get_system_by_type(self.config, "ERP")
        self.host = self.sys_config["host"]
        self.user = self.sys_config["credentials"]["username"]
        self.password = self.sys_config["credentials"]["password"]
        self.client = self.sys_config["client"]
        self.service = service
        self.entity_set = entity_set

        self.endpoint = (
            f"{self.host}/sap/opu/odata/sap/{self.service}/{self.entity_set}"
        )

        credentials = f"{self.user}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode(
            "utf-8"
        )

        self.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        self.params = {"sap-client": self.client, "$format": "json"}

    def get_csrf_token(self):

        headers = {"x-csrf-token": "FETCH"}

        headers.update(self.headers)

        params = {"$top": 1, "$skip": 0}
        params.update(self.params)

        response = requests.get(
            self.endpoint, headers=headers, params=params, verify=False
        )

        if response.status_code != 200:
            raise APIException(
                endpoint=self.endpoint,
                status_code=response.status_code,
                response=response.text,
            )

        token = response.headers.get("x-csrf-token")
        cookies = response.cookies
        return token, cookies


# Exception Class for API Errors
class APIException(Exception):
    """
    Exception class for API calls. You can use the following attributes of the APIException instance.

    Attributes:
        endpoint:
            The URL endpoint with which the APIException has occurred
        status_cde:
            Status code returned by the API call
        response:
            Response (generally json) returned by the API call
    """

    def __init__(self, endpoint, status_code, response):

        self.endpoint = endpoint
        self.status_code = status_code
        self.response = response

        super().__init__(f"{endpoint} failed with status {status_code} : {response}")
