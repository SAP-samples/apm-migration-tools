# imports
import requests
import urllib3

# custom imports
from modules.util.api import ERPClient, APIException
from modules.util.helpers import Logger


class ApiCharacteristicHeader:

    """
    A class to interact with the SAP API_CLFN_CHARACTERISTIC_SRV service.
    Attributes:
        api_client (ERPClient): An instance of the ERPClient to handle API requests.
        endpoint (str): The API endpoint URL.
        headers (dict): The headers to be used in API requests.
        params (dict): The parameters to be used in API requests.
        log (Logger): Logger instance for logging API interactions.
    Methods:
        search_characteristic(characteristic: str):
            Searches for a characteristic in the SAP system.
            Args:
                characteristic (str): The characteristic to search for.
            Returns:
                dict: The first result of the search if found, otherwise None.
            Raises:
                Exception: If the API call fails.
        create_characteristic(char: str, datatype: str, description: str, length=None, decimals=None):
            Creates a new characteristic in the SAP system.
            Args:
                char (str): The characteristic to create.
                datatype (str): The data type of the characteristic.
                description (str): The description of the characteristic.
                length (int, optional): The length of the characteristic. Defaults to None.
                decimals (int, optional): The number of decimals for the characteristic. Defaults to None.
            Returns:
                dict: The created characteristic data.
            Raises:
                Exception: If the API call fails.
    """

    def __init__(self, config_id: str):

        """
        Initializes the S4ClfnCharacteristicSrv class.
        Args:
            config_id (str): The configuration ID used to initialize the ERPClient.
        Attributes:
            api_client (ERPClient): An instance of ERPClient initialized with the provided config_id, service, and entity_set.
            endpoint (str): The endpoint URL of the API client.
            headers (dict): The headers used in the API client requests.
            params (dict): The parameters used in the API client requests.
            log (Logger): A logger instance for logging messages.
        Notes:
            If the API client is configured to ignore SSL certificate warnings, these warnings will be disabled.
        """

        service = "API_CLFN_CHARACTERISTIC_SRV"
        entity_set = "A_ClfnCharacteristicForKeyDate"

        self.api_client = ERPClient(
            config_id=config_id, service=service, entity_set=entity_set
        )

        self.endpoint = self.api_client.endpoint
        self.headers = self.api_client.headers
        self.params = self.api_client.params

        if self.api_client.ignore_cert:
            urllib3.disable_warnings(
                urllib3.exceptions.InsecureRequestWarning
            )  # for testing purposes only

        self.log = Logger.get_logger(config_id)

    def search_characteristic(self, characteristic: str):

        """
        Searches for a characteristic in the ERP system.
        Args:
            characteristic (str): The characteristic to search for.
        Returns:
            dict: The first result of the search if found, otherwise None.
        Raises:
            APIException: If the API call returns a status code other than 200.
            Exception: If there is any other issue with the API call.
        """

        params = {}
        params.update(self.params)

        headers = {}
        headers.update(self.headers)

        if characteristic:
            params["$filter"] = f"Characteristic eq '{characteristic}'"

        try:
            res = requests.get(
                url=self.endpoint,
                headers=headers,
                params=params,
                timeout=self.api_client.timeout,
                verify=False,
            )
            self.log.debug(f"[GET] Search for Characteristic {characteristic}")
            if res.status_code != 200:
                raise APIException(
                    endpoint=self.endpoint,
                    status_code=res.status_code,
                    response=res.text,
                )
            data = res.json()
            results = data.get("d").get("results")
            if results:
                return results[0]
        except Exception as e:
            raise Exception(f"API call failed: {e}")

    def create_characteristic(
        self,
        char: str,
        datatype: str,
        description: str,
        length=None,
        decimals=None,
        negative_flag=False,
        case_sensitive_flag=False,
    ):

        """
        Creates a characteristic in the ERP system.
        Args:
            char (str): The name of the characteristic.
            datatype (str): The data type of the characteristic.
            description (str): The description of the characteristic.
            length (int, optional): The length of the characteristic. Defaults to None.
            decimals (int, optional): The number of decimal places for the characteristic. Defaults to None.
            negative_flag (bool, optional): Flag indicating if negative values are allowed. Defaults to False.
            case_sensitive_flag (bool, optional): Flag indicating if the characteristic is case sensitive. Defaults to False.
        Returns:
            dict: The response data from the API call.
        Raises:
            APIException: If the API call does not return a status code of 201.
            Exception: If any other error occurs during the API call.
        """

        params = {}
        params.update(self.params)
        params.pop("$format", None)

        csrf_token, cookies = self.api_client.get_csrf_token()

        headers = {"x-csrf-token": csrf_token, "X-Requested-With": "XMLHttpRequest"}
        headers.update(self.headers)

        body = {
            "Characteristic": char,
            "CharcStatus": "1",
            "CharcDataType": datatype,
            "CharcLength": int(length) if length else 0,
            "CharcDecimals": int(decimals) if decimals else 0,
            "NegativeValueIsAllowed": negative_flag,
            "ValueIsCaseSensitive": case_sensitive_flag,
            "to_CharacteristicDesc": {
                "results": [{"Language": "EN", "CharcDescription": description}]
            },
        }

        try:
            res = requests.post(
                url=self.endpoint,
                headers=headers,
                params=params,
                json=body,
                timeout=self.api_client.timeout,
                cookies=cookies,
                verify=False,
            )
            self.log.debug(f"[POST] Create Characteristic {char}")
            if res.status_code != 201:
                raise APIException(
                    endpoint=self.endpoint,
                    status_code=res.status_code,
                    response=res.text,
                )
            data = res.json()
            return data.get("d")
        except Exception as e:
            raise Exception(f"API call failed: {e}")

    def delete_characteristic(self, guid: str) -> None:

        """
        Deletes a characteristic identified by the given GUID.
        This method sends a DELETE request to the API endpoint to remove the characteristic.
        It handles CSRF token retrieval and constructs the necessary headers and parameters
        for the request. If the deletion is unsuccessful, an APIException is raised.
        Args:
            guid (str): The GUID of the characteristic to be deleted.
        Raises:
            APIException: If the API response status code is not 204 (No Content).
            Exception: If there is any other exception during the API call.
        """

        params = {}
        params.update(self.params)
        params.pop("$format", None)

        csrf_token, cookies = self.api_client.get_csrf_token()

        headers = {"x-csrf-token": csrf_token, "X-Requested-With": "XMLHttpRequest"}
        headers.update(self.headers)
        url = f"{self.endpoint}('{guid}')"
        try:
            res = requests.delete(
                url=url,
                headers=headers,
                params=params,
                timeout=self.api_client.timeout,
                cookies=cookies,
                verify=False,
            )
            self.log.debug(f"[DELETE] Delete Characteristic {guid}")
            if res.status_code != 204:
                raise APIException(
                    endpoint=self.endpoint,
                    status_code=res.status_code,
                    response=res.text,
                )
        except Exception as e:
            raise Exception(f"API call failed: {e}")
