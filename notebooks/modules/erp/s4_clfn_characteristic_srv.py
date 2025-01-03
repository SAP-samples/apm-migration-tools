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
