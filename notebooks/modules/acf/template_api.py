"""
TEMPLATE API module for migration tooling.
SAP API Documentation: https://api.sap.com/api/TemplateAPI
"""
# standard imports
import requests

# custom imports
from modules.util.api import ACFClient, APIException
from modules.util.helpers import Logger


class ApiIndicator:

    """
    API Indicator Class that contains attributes & methods relevant for Indicator APIs.
    SAP API Documentation: https://api.sap.com/api/TemplateAPI/resource/Indicator
    """

    def __init__(self, config_id: str):

        """
        Initializes the class object with necessary variables and utility module objects
        """

        self.api_client = ACFClient(config_id=config_id)
        self.indicators_endpoint = f"{self.api_client.base_url}/indicators"
        self.indicatorgroups_endpoint = self.api_client.base_url + "/indicatorgroups"
        self.template_endpoint = self.api_client.base_url + "/templates"
        self.log = Logger.get_logger(config_id)

    def _get_total_count(self, endpoint):

        """
        Get total count of objects of a specific endpoint

        Visibility: Private

        Parameters:
            endpoint: Specifies the endpoint of the URL (complete API URL)

        Returns:
            count(int): Integer variable containing the count of objects
        """

        api_url = endpoint + "/$count"
        headers = {"Authorization": f"Bearer {self.api_client.get_token()}"}
        response = requests.get(
            api_url, headers=headers, timeout=self.api_client.timeout
        )
        response.raise_for_status()
        return int(response.text)

    def _get_response(self, endpoint):

        """
        Generic function to get response of a GET API call based on endpoint

        Visibility: Private

        Parameters:
            endpoint: Specifies the endpoint of the URL (complete API URL)

        Returns:
            response(list): Response of the API Call
        """

        headers = {
            "Authorization": f"Bearer {self.api_client.get_token()}",
            "Content-Type": "application/json",
        }

        res = requests.get(
            url=endpoint, headers=headers, timeout=self.api_client.timeout
        )

        if res.status_code != 200:
            raise APIException(
                endpoint=endpoint, status_code=res.status_code, response=res.text
            )
        return res.json()

    def get_indicators_count(self):

        """
        Get count of Indicators from the system
        """

        return self._get_total_count(self.indicators_endpoint)

    def get_indicators(self):

        """
        Get list of indicators from the system
        """

        return self._get_response(self.indicators_endpoint)

    def get_indicator_indicator_id(self, id: str):

        """
        Get details for a particular Indicator ID from the system

        Parameters:
            id(str): GUID of the Indicator for which the data has to be obtained from the system
        """

        url = f"{self.indicators_endpoint}/{id}"
        return self._get_response(url)

    def get_indicatorgroups_count(self):

        """
        Get count of Indicator Groups from the system
        """

        return self._get_total_count(self.indicatorgroups_endpoint)

    def get_indicatorgroups(self):

        """
        Get list of indicator groups from the system

        Parameters:
            top(int, optional): number of records that needs to be fetched (pagination - top). **Defaults to 5000**
            skip(int, optional): number of records to be skipped while fetching (pagination - skip). **Defaults to 0**
        """

        return self._get_response(self.indicatorgroups_endpoint)

    def get_indicatorgroup_id(self, guid: str):

        """
        Get indicators within an indicator group from the system

        Parameters:
            guid(str): GUID of the Indicator Group ID

        Returns:
            response(json): API Response in JSON format
        """

        headers = {
            "Authorization": f"Bearer {self.api_client.get_token()}",
            "Content-Type": "application/json",
        }

        api_url = f"{self.indicatorgroups_endpoint}/{guid}"
        res = requests.get(api_url, headers=headers, timeout=self.api_client.timeout)

        if res.status_code != 200:

            raise APIException(
                endpoint=api_url, status_code=res.status_code, response=res.text
            )
        data = res.json()
        if data:
            return data


class ApiTemplate:

    """
    ApiTemplate class to interact with the ACF API for template-related operations.
    Methods:
        __init__(config_id: str):
            Initializes the ApiTemplate object with the given configuration ID.
        get_template_template_id(guid: str):
            Retrieves template details from the system using the provided GUID.
    """

    def __init__(self, config_id: str):

        """
        Initializes the class object with necessary variables and utility module objects
        """

        self.api_client = ACFClient(config_id=config_id)
        self.endpoint = f"{self.api_client.base_url}/templates"
        self.log = Logger.get_logger(config_id)

    def get_template_template_id(self, guid: str):

        """
        Get template details from the system

        Parameters:
            guid(str): GUID of the Template ID

        Returns:
            response(json): API Response in JSON format
        """

        headers = {
            "Authorization": f"Bearer {self.api_client.get_token()}",
            "Content-Type": "application/json",
        }

        api_url = f"{self.endpoint}/{guid}"
        res = requests.get(api_url, headers=headers, timeout=self.api_client.timeout)
        self.log.debug(f"[GET] Template for Template ID {guid}")
        if res.status_code != 200:
            raise APIException(
                endpoint=api_url, status_code=res.status_code, response=res.text
            )
        data = res.json()
        if data:
            return data
