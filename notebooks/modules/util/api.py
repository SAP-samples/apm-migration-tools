# standard imports
import time
import base64
from typing import Optional
import requests

# custom imports
from modules.util.config import get_config_by_id, get_system_by_type


class BaseAPIClient:

    """
    BaseAPIClient is a class that provides a base implementation for an API client. It handles authentication using client credentials and manages the retrieval and expiration of authentication tokens.
    Methods:
        __init__(client_id, client_secret, token_url, base_url, x_api_key=None):
            Initializes the API client with the given credentials and configuration.
        get_token():
            Retrieves an authentication token. If the current token is expired or not set, it authenticates using client credentials and fetches a new token from the token URL.
    """

    def __init__(
        self,
        client_id,
        client_secret,
        token_url,
        base_url,
        x_api_key: Optional[str] = None,
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

        if self.token_expiry is None or time.time() >= self.token_expiry:
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

        """
        Initializes the API client with the given configuration ID and system type.
        Args:
            config_id (str): The ID of the configuration to use.
            system_type (str): The type of the system to connect to.
        Raises:
            ValueError: If the system type is not found in the configuration.
        """

        self.config = get_config_by_id(config_id)
        self.sys_config = get_system_by_type(self.config, system_type)

        if self.sys_config is None:
            raise ValueError(f"System type {system_type} not found in configuration")

        super().__init__(
            base_url=self.sys_config["host"],
            client_id=self.sys_config["credentials"]["client_id"],
            client_secret=self.sys_config["credentials"]["client_secret"],
            token_url=self.sys_config["credentials"]["token_url"],
            x_api_key=self.sys_config.get("credentials", {}).get("x_api_key"),
        )

    def get(
        self, endpoint: str, params: dict = None, headers: dict = None
    ) -> requests.Response:
        _headers = {
            "Authorization": f"Bearer {super().get_token()}",
            "Content-Type": "application/json",
        }

        # add the headers from the function call
        if headers:
            _headers.update(headers)

        res = requests.get(
            url=endpoint, headers=_headers, params=params, timeout=self.timeout
        )
        if not res.status_code // 100 == 2:
            raise APIException(
                endpoint=endpoint, status_code=res.status_code, response=res.text
            )
        else:
            return res

    def post(
        self, endpoint: str, params: dict = None, headers: dict = None, files=None
    ) -> requests.Response:
        _headers = {
            "Authorization": f"Bearer {super().get_token()}",
        }

        # add the headers from the function call
        if headers:
            _headers.update(headers)

        res = requests.post(
            url=endpoint,
            headers=_headers,
            params=params,
            timeout=self.timeout,
            files=files,
        )
        if not res.status_code // 100 == 2:
            raise APIException(
                endpoint=endpoint, status_code=res.status_code, response=res.text
            )
        else:
            return res

    def get_batches(
        self,
        endpoint: str,
        batch_size: int = 100,
        filter: Optional[str] = None,
        expand: Optional[str] = None,
    ):

        """
        Retrieve data from an API endpoint in batches.
        Args:
            endpoint (str): The API endpoint to retrieve data from.
            batch_size (int, optional): The number of records to retrieve per batch. Defaults to 100.
            filter (Optional[str], optional): OData filter query to apply. Defaults to None.
            expand (Optional[str], optional): OData expand query to apply. Defaults to None.
        Returns:
            list: A list of records retrieved from the API.
        Raises:
            APIException: If the API response status code is not 200.
            Exception: If any other error occurs during the API call.
        """

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
                res = requests.get(
                    url=api_url, headers=headers, params=params, timeout=self.timeout
                )
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

    """
    A client for interacting with the ACF API.
    Inherits from:
        APIClient: A base class for API clients.
    Attributes:
        base_url (str): The base URL for the ACF API.
        erp_config (dict): The ERP system configuration.
        erp_ssid (str): The ERP system ID and client.
    Methods:
        __init__(config_id: str): Initializes the ACFClient with the given configuration ID.
    """

    def __init__(self, config_id: str):

        """
        Initializes the ACFClient with the given configuration ID.
        Args:
            config_id (str): The configuration ID for the ACFClient.
        Raises:
            ValueError: If the ERP system is not found in the configuration.
        """

        super().__init__(config_id, "ACF")
        self.base_url = f"{self.base_url}/ain/services/api/v1"

        self.erp_config = get_system_by_type(self.config, "ERP")
        if self.erp_config is None:
            raise ValueError("ERP system not found in configuration")
        self.erp_ssid = (
            f"{str(self.erp_config['sys_id']).upper()}_{self.erp_config['client']}"
        )


class APMClient(APIClient):

    """
    A client for interacting with the APM service.
    Inherits from APIClient and initializes the base URL for the APM service.
    Attributes:
        base_url (str): The base URL for the APM service.
        erp_config (dict): The ERP system configuration.
        erp_ssid (str): The ERP system ID and client.
    Methods:
        __init__(config_id: str, service: str):
            Initializes the APMClient with the given configuration ID and service.
            Raises ValueError if the ERP system is not found in the configuration.
    """

    def __init__(self, config_id: str, service: str):

        """
        Initializes the APMClient with the given configuration ID and service.
        Args:
            config_id (str): The configuration ID.
            service (str): The service name.
        Raises:
            ValueError: If the ERP system is not found in the configuration.
        """

        super().__init__(config_id, "APM")
        self.base_url = f"{self.base_url}/{service}/v1"

        self.erp_config = get_system_by_type(self.config, "ERP")
        if self.erp_config is None:
            raise ValueError("ERP system not found in configuration")
        self.erp_ssid = (
            f"{str(self.erp_config['sys_id']).upper()}_{self.erp_config['client']}"
        )


class ERPClient:

    """
    A client for interacting with an ERP system using OData services.
    Attributes:
        config (dict): Configuration details for the ERP system.
        sys_config (dict): System configuration details for the ERP system.
        host (str): The host URL of the ERP system.
        user (str): The username for authentication.
        password (str): The password for authentication.
        client (str): The client number for the ERP system.
        ignore_cert (bool): Whether to ignore SSL certificate verification.
        service (str): The OData service name.
        entity_set (str): The OData entity set name.
        timeout (int): The timeout for HTTP requests.
        endpoint (str): The full endpoint URL for the OData service.
        headers (dict): The HTTP headers for requests.
        params (dict): The query parameters for requests.
    Methods:
        get_csrf_token():
            Fetches a CSRF token from the ERP system.
            Returns:
                tuple: A tuple containing the CSRF token and cookies.
            Raises:
                APIException: If the request fails.
    """

    def __init__(self, config_id: str, service: str, entity_set: str):

        """
        Initializes the API client with the given configuration ID, service, and entity set.
        Args:
            config_id (str): The configuration ID to retrieve the system configuration.
            service (str): The OData service name.
            entity_set (str): The OData entity set name.
        Raises:
            ValueError: If the ERP system is not found in the configuration.
        Attributes:
            config (dict): The configuration dictionary retrieved by the configuration ID.
            sys_config (dict): The system configuration dictionary for the ERP system.
            host (str): The host URL of the ERP system.
            user (str): The username for authentication.
            password (str): The password for authentication.
            client (str): The SAP client number.
            ignore_cert (bool): Whether to ignore SSL certificate validation.
            service (str): The OData service name.
            entity_set (str): The OData entity set name.
            timeout (int): The request timeout in seconds.
            endpoint (str): The full OData service endpoint URL.
            headers (dict): The HTTP headers for the request, including authorization.
            params (dict): The query parameters for the request.
        """

        self.config = get_config_by_id(config_id)
        self.sys_config = get_system_by_type(self.config, "ERP")
        if self.sys_config is None:
            raise ValueError("ERP system not found in configuration")
        self.host = self.sys_config["host"]
        self.user = self.sys_config["credentials"]["username"]
        self.password = self.sys_config["credentials"]["password"]
        self.client = self.sys_config["client"]
        self.ignore_cert = self.sys_config["ignore_cert"]
        self.service = service
        self.entity_set = entity_set
        self.timeout = 30

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

        """
        Fetches a CSRF token from the API endpoint.
        This method sends a GET request to the specified endpoint with the
        headers and parameters provided. It expects the server to return a
        CSRF token in the response headers.
        Returns:
            tuple: A tuple containing the CSRF token and cookies from the response.
        Raises:
            APIException: If the response status code is not 200.
        """

        headers = {"x-csrf-token": "FETCH"}
        headers.update(self.headers)
        params = {"$top": 1, "$skip": 0}
        params.update(self.params)

        response = requests.get(
            self.endpoint,
            headers=headers,
            params=params,
            timeout=self.timeout,
            verify=False,
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
    Exception class for API calls.
    You can use the following attributes of the APIException instance.

    Attributes:
        endpoint:
            The URL endpoint with which the APIException has occurred
        status_cde:
            Status code returned by the API call
        response:
            Response (generally json) returned by the API call
    """

    def __init__(self, endpoint, status_code, response):

        """
        Initialize the API error with endpoint, status code, and response.
        Args:
            endpoint (str): The API endpoint that was called.
            status_code (int): The HTTP status code returned by the API.
            response (str): The response message from the API.
        """

        self.endpoint = endpoint
        self.status_code = status_code
        self.response = response

        super().__init__(f"{endpoint} failed with status {status_code} : {response}")
