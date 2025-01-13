import requests
from modules.util.api import ERPClient, APIException
import urllib3
from modules.util.helpers import Logger


class API_CharacteristicHeader:
    def __init__(self, config_id: str):
        service = "API_CLFN_CHARACTERISTIC_SRV"
        entity_set = "A_ClfnCharacteristicForKeyDate"

        self.api_client = ERPClient(
            config_id=config_id, service=service, entity_set=entity_set
        )

        self.endpoint = self.api_client.endpoint
        self.headers = self.api_client.headers
        self.params = self.api_client.params

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
                url=self.endpoint, headers=headers, params=params, verify=False
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
        self, char: str, datatype: str, description: str, length=None, decimals=None
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
