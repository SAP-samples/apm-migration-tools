# standard imports
import requests

# custom imports
from modules.util.api import APMClient, APIException
from modules.util.helpers import Logger

"""
SAP API Documentation: https://api.sap.com/api/Indicator_Related_APIs/resource/Indicator_Positions
"""


class ApiIndicatorPosition:

    """
    A class to manage indicator positions using the APM system's API.
    Methods:
    __init__(config_id: str)
        Initializes the class object with necessary variables and utility module objects.
    get_indicator_positions()
        Retrieves a list of indicator positions from the system.
    get_indicator_positions_count() -> int
        Retrieves the count of indicator positions from the system.
    create_indicator_position(name: str)
        Creates a new indicator position in the APM system.
    get_indicator_position_name(name: str) -> dict
    """

    def __init__(self, config_id: str):

        """
        Initializes the class object with necessary variables and utility module objects
        """

        self.api_client = APMClient(config_id=config_id, service="IndicatorService")
        self.endpoint = f"{self.api_client.base_url}"
        self.log = Logger.get_logger(config_id)

    def get_indicator_positions(self):

        """
        Get list of indicators positions from the system
        """

        headers = {
            "Authorization": f"Bearer {self.api_client.get_token()}",
            "Content-Type": "application/json",
            "x-api-key": self.api_client.x_api_key,
        }

        response = []
        endpoint_suffix = "/IndicatorPositions"
        while True:
            api_url = f"{self.endpoint}{endpoint_suffix}"
            res = requests.get(
                url=api_url, timeout=self.api_client.timeout, headers=headers
            )
            if res.status_code != 200:
                raise APIException(
                    endpoint=api_url, status_code=res.status_code, response=res.text
                )
            data = res.json()
            response.extend(data["value"])

            if "@nextLink" in data:
                endpoint_suffix = f"/{data['@nextLink']}"
            else:
                break
        self.log.info(f"[GET] Indicator Positions: {len(response)}")
        return response

    def get_indicator_positions_count(self) -> int:

        """
        Get count of indicators positions from the system
        """

        headers = {
            "Authorization": f"Bearer {self.api_client.get_token()}",
            "Content-Type": "application/json",
            "x-api-key": self.api_client.x_api_key,
        }

        api_url = f"{self.api_client.base_url}/IndicatorPositions/$count"
        response = requests.get(
            api_url, timeout=self.api_client.timeout, headers=headers
        )
        response.raise_for_status()
        return int(response.text)

    def create_indicator_position(self, name: str):

        """
        Method to create Indicator Positions in the APM system

        Visibility: Public

        Parameters:
            ssid: Logical System ID with which data needs to be posted
            name: Name of the Indicator Position

        Returns:
            guid: newly created GUID for Indicator Position
        """

        response = []
        suffix = "/IndicatorPositions"

        api_url = f"{self.api_client.base_url}{suffix}"

        headers = {
            "Authorization": f"Bearer {self.api_client.get_token()}",
            "Content-Type": "application/json",
            "x-api-key": self.api_client.x_api_key,
        }

        body = {"SSID": self.api_client.erp_ssid, "name": name}

        res = requests.post(
            url=api_url, timeout=self.api_client.timeout, json=body, headers=headers
        )

        if res.status_code != 201:
            raise APIException(
                endpoint=api_url, status_code=res.status_code, response=res.text
            )

        response = res.json()
        return response

    def get_indicator_position_name(self, name: str) -> dict:

        """
        Retrieves the position details of an indicator by its name.
        Args:
            name (str): The name of the indicator.
        Returns:
            dict: A dictionary containing the position details of the indicator if found, otherwise None.
        Raises:
            APIException: If the API request fails or returns a status code other than 200.
        """

        headers = {
            "Authorization": f"Bearer {self.api_client.get_token()}",
            "Content-Type": "application/json",
            "x-api-key": self.api_client.x_api_key,
        }

        params = {"$filter": f"name eq '{name.upper()}'"}  ##assume: name is upper case

        api_url = f"{self.api_client.base_url}/IndicatorPositions"
        response = requests.get(
            api_url, timeout=self.api_client.timeout, headers=headers, params=params
        )

        if response.status_code != 200:
            raise APIException(
                endpoint=api_url,
                status_code=response.status_code,
                response=response.text,
            )

        data = response.json()
        if "value" in data and len(data["value"]) > 0:
            return data["value"][0]  ##assume: only one record per name
        return {}


"""
SAP API Documentation: https://api.sap.com/api/Indicator_Related_APIs/resource/Indicators
"""


class ApiIndicators:

    """
    A class to manage API interactions related to indicators.
    Attributes:
        api_client (APMClient): The API client for making requests.
        endpoint (str): The endpoint URL for the IndicatorService.
        headers (dict): The headers to be used in API requests.
    Methods:
        __init__(config_id: str):
            Initializes the class with the given configuration ID.
        create_indicator(row: dict) -> dict:
            Creates a new indicator using the provided row data.
        search_indicator(
            characteristics_SSID: str
        ) -> dict:
            Searches for an indicator based on the provided parameters.
    """

    def __init__(self, config_id: str):

        """
        Initializes the class object with necessary variables and utility module objects
        """

        self.api_client = APMClient(config_id=config_id, service="IndicatorService")
        self.endpoint = f"{self.api_client.base_url}/Indicators"
        self.headers = {
            "Authorization": f"Bearer {self.api_client.get_token()}",
            "Content-Type": "application/json",
            "x-api-key": self.api_client.x_api_key,
        }

    def create_indicator(self, row):

        """
        Creates an indicator using the provided row data.
        Args:
            row (dict): A dictionary containing the following keys:
                - technicalObject_number (str): The technical object number.
                - technicalObject_SSID (str): The technical object SSID.
                - technicalObject_type (str): The technical object type.
                - category_SSID (str): The category SSID.
                - category_name (str): The category name.
                - characteristics_SSID (str): The characteristics SSID.
                - characteristics_characteristicsInternalId (str): The characteristics internal ID.
                - positionDetails_ID (str): The position details ID.
        Returns:
            dict: The JSON response from the API if the indicator is created successfully.
        Raises:
            APIException: If the API response status code is not 201.
        """

        body = {
            "technicalObject_number": row.get("technicalObject_number"),
            "technicalObject_SSID": row.get("technicalObject_SSID"),
            "technicalObject_type": row.get("technicalObject_type"),
            "category_SSID": row.get("category_SSID"),
            "category_name": row.get("category_name"),
            "characteristics_SSID": row.get("characteristics_SSID"),
            "characteristics_characteristicsInternalId": row.get(
                "characteristics_characteristicsInternalId"
            ),
            "positionDetails_ID": row.get("positionDetails_ID"),
        }

        res = requests.post(
            headers=self.headers,
            url=self.endpoint,
            json=body,
            timeout=self.api_client.timeout,
        )
        if res.status_code != 201:
            raise APIException(
                endpoint=self.endpoint, status_code=res.status_code, response=res.text
            )
        return res.json()

    def search_indicator(
        self,
        technicalObject_number: str,
        technicalObject_type: str,
        technicalObject_SSID: str,
        category_name: str,
        category_SSID: str,
        characteristics_characteristicsInternalId: str,
        positionDetails_ID: str,
        characteristics_SSID: str,
    ):

        """
        Searches for an indicator based on the provided parameters.
        Args:
            technicalObject_number (str): The number of the technical object.
            technicalObject_type (str): The type of the technical object.
            technicalObject_SSID (str): The SSID of the technical object.
            category_name (str): The name of the category.
            category_SSID (str): The SSID of the category.
            characteristics_characteristicsInternalId (str): The internal ID of the characteristics.
            positionDetails_ID (str): The ID of the position details.
            characteristics_SSID (str): The SSID of the characteristics.
        Returns:
            dict: The JSON response from the API containing the search results.
        Raises:
            APIException: If the API request fails with a status code other than 200.
        """

        params = {
            "$filter": f"technicalObject_number eq '{technicalObject_number}' and technicalObject_type eq '{technicalObject_type}' and technicalObject_SSID eq '{technicalObject_SSID}' and category_name eq '{category_name}' and category_SSID eq '{category_SSID}' and characteristics_characteristicsInternalId eq '{characteristics_characteristicsInternalId}' and positionDetails_ID eq '{positionDetails_ID}' and characteristics_SSID eq '{characteristics_SSID}'"
        }

        res = requests.get(
            url=self.endpoint,
            headers=self.headers,
            params=params,
            timeout=self.api_client.timeout,
        )
        if res.status_code != 200:
            raise APIException(
                endpoint=self.endpoint, status_code=res.status_code, response=res.text
            )
        return res.json()


"""
SAP API Documentation: https://api.sap.com/api/Indicator_Related_APIs/resource/Indicators
"""


class ApiCharacteristics:

    """
    A class to interact with the IndicatorService API for managing characteristics.
    Attributes:
        api_client (APMClient): An instance of APMClient configured for the IndicatorService.
        endpoint (str): The API endpoint for Indicators.
        headers (dict): The headers required for making API requests.
    Methods:
        __init__(config_id: str):
            Initializes the ApiCharacteristics instance with the given configuration ID.
        search_characteristic(internalId: str):
            Searches for a characteristic by its internal ID.
    """

    def __init__(self, config_id: str):

        """
        Initializes the class object with necessary variables and utility module objects
        """

        self.api_client = APMClient(config_id=config_id, service="IndicatorService")
        self.endpoint = f"{self.api_client.base_url}/Indicators"
        self.headers = {
            "Authorization": f"Bearer {self.api_client.get_token()}",
            "Content-Type": "application/json",
            "x-api-key": self.api_client.x_api_key,
        }

    def search_characteristic(self, internalId: str):

        """
        Searches for a characteristic by its internal ID.
        Args:
            internalId (str): The internal ID of the characteristic to search for.
        Returns:
            dict: The JSON response from the API containing the characteristic details.
        Raises:
            APIException: If the API request fails with a status code other than 200.
        """

        url = f"{self.api_client.base_url}/Characteristics(SSID='{self.api_client.erp_ssid}',characteristicsInternalId='{internalId}')"
        res = requests.get(
            url=url,
            headers=self.headers,
            timeout=self.api_client.timeout,
        )

        if res.status_code != 200:
            raise APIException(
                endpoint=url, status_code=res.status_code, response=res.text
            )

        return res.json()
