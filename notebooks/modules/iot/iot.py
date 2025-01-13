# Description: A wrapper class for interacting with the SAP IoT API.
import requests
from modules.util.config import get_config_by_id, get_system_by_type

# pylint: disable=relative-beyond-top-level
from modules.base_class import BaseAPIWrapper


class SAPIoTAPIWrapper(BaseAPIWrapper):
    """
    A wrapper class for interacting with the SAP IoT API.

    Methods
    -------
    __init__(base_url=None)
        Initializes the SAPIoTAPIWrapper with the given base URL.

    get_property_set_types()
        Retrieves all property set types from the SAP IoT API.

    get_thing_type_by_external_id(external_id)
        Retrieves the thing type by its external ID from the SAP IoT API.
    """

    def __init__(self, config_id: str):
        self.config = get_config_by_id(config_id)
        self.iot_config = get_system_by_type(self.config, "IOT")
        super().__init__(
            self.iot_config["credentials"]["client_id"],
            self.iot_config["credentials"]["client_secret"],
            self.iot_config["credentials"]["token_url"],
            None,
        )

    def get_property_set_types(self):
        # get all property set types
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "accept": "application/json",
        }
        # Construct the full URL with filters, top, and skip parameters
        base_url = self.iot_config["iot_endpoints"]["config_thing"]
        url = f"{base_url}/ThingConfiguration/v1/PropertySetTypes"

        # Make the request to the endpoint
        response = requests.get(url, headers=headers, timeout=self.timeout)

        # Raise an exception if the request failed
        if response.status_code != 200:
            response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        if data["d"]:
            return data["d"]
        elif data["error"]:
            # throw an error if there is an error
            raise requests.exceptions.HTTPError(data["error"]["code"])
        else:
            return None

    def get_thing_type_by_external_id(self, external_id):
        # get thing type by external id
        headers = {
            "Authorization": f"Bearer {self.token}",
            "accept": "application/json",
        }
        # Construct the full URL with filters, top, and skip parameters
        base_url = self.iot_config["iot_endpoints"]["thing"]
        url = f"{base_url}/Things?$filter=_externalId eq '{external_id}'"

        # Make the request to the endpoint
        response = requests.get(url, headers=headers, timeout=self.timeout)

        # Raise an exception if the request failed
        if response.status_code != 200:
            response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        if data["value"]:
            return data["value"][0]
        else:
            return None

    def get_thing_types(self) -> list:
        """
        Retrieves all thing types from the SAP IoT API.

        Returns:
            list: A list of thing types if successful, otherwise None.

        Raises:
            requests.exceptions.RequestException: If the HTTP request fails.
        """
        # get all thing types
        headers = {
            "Authorization": f"Bearer {self.token}",
            "accept": "application/json",
        }

        # Construct the full URL with filters, top, and skip parameters
        url = f"{self.iot_config['iot_endpoints']['config_thing']}/ThingConfiguration/v1/ThingTypes"

        # Make the request to the endpoint
        response = requests.get(url, headers=headers, timeout=self.timeout)

        # Raise an exception if the request failed
        if response.status_code != 200:
            response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        if data["d"] and len(data["d"]["results"]) > 0:
            # iterate through the results and return the thing types names
            return [thing_type["Name"] for thing_type in data["d"]["results"]]
        elif data["error"]:
            # throw an error if there is an error
            raise requests.exceptions.HTTPError(data["error"]["code"])
        else:
            return None

    def get_property_sets_by_thing_type(self, thing_type: str) -> list:
        # get property set by thing type
        headers = {
            "Authorization": f"Bearer {self.token}",
            "accept": "application/json",
        }

        # Construct the full URL with filters, top, and skip parameters
        base_url = self.iot_config["iot_endpoints"]["config_thing"]
        url = f"{base_url}/ThingConfiguration/v1/ThingTypes('{thing_type}')?$expand=PropertySets"

        # Make the request to the endpoint
        response = requests.get(url, headers=headers, timeout=self.timeout)

        # Raise an exception if the request failed
        if response.status_code != 200:
            response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        if data["d"]:
            # filter the response to only return the property sets with "DataCategory": "TimeSeriesData"
            return [
                property_set["PropertySetType"]
                for property_set in data["d"]["PropertySets"]["results"]
                if property_set["DataCategory"] == "TimeSeriesData"
            ]
        elif data["error"]:
            # throw an error if there is an error
            raise requests.exceptions.HTTPError(data["error"]["code"])
        else:
            return None

    def initiate_time_series_export(
        self, property_set_type: str, start_date: str, end_date: str
    ) -> str:
        """
        Initiates the export of time series data for a specified property set type within a given date range.

        Args:
            property_set_type (str): The type of property set to export.
            start_date (str): The start date for the time series data export in the format 'YYYY-MM-DD'.
            end_date (str): The end date for the time series data export in the format 'YYYY-MM-DD'.

        Returns:
            str: The response ID of the initiated data export if successful, otherwise None.

        Raises:
            requests.exceptions.RequestException: If the HTTP request fails.
        """
        # initiate time series export
        headers = {
            "Authorization": f"Bearer {self.token}",
            "accept": "application/json",
        }

        # Construct the full URL with filters, top, and skip parameters
        base_url = self.iot_config["iot_endpoints"]["cold_store"]
        url = f"{base_url}/v1/InitiateDataExport/{property_set_type}?timerange={start_date}-{end_date}"

        response = requests.post(url, headers=headers, timeout=self.timeout)

        # Raise an exception if the request failed
        if response.status_code != 200:
            response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        if "RequestId" in data:
            return data["RequestId"]
        else:
            return None

    def get_time_series_export_status(self, request_id: str) -> str:
        """
        Retrieves the status of a time series data export request.

        Args:
            request_id (str): The request ID of the initiated data export.

        Returns:
            str: The status of the data export request if successful, otherwise None.

        Raises:
            requests.exceptions.RequestException: If the HTTP request fails.
        """
        # get time series export status
        headers = {
            "Authorization": f"Bearer {self.token}",
            "accept": "application/json",
        }

        # Construct the full URL with filters, top, and skip parameters
        base_url = self.iot_config["iot_endpoints"]["cold_store"]
        url = f"{base_url}/v1/DataExportStatus?requestId={request_id}"

        response = requests.get(url, headers=headers, timeout=self.timeout)

        # Raise an exception if the request failed
        if response.status_code != 200:
            response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        if "Status" in data:
            if data["Status"] == "The file is available for download.":
                data["Status"] = "Ready for Download"

            return data["Status"]
        else:
            return None

    def download_time_series_export(self, request_id: str) -> str:
        """
        Downloads the time series data export for a specified request ID.

        Args:
            request_id (str): The request ID of the initiated data export.

        Returns:
            str: The download URL of the data export if successful, otherwise None.

        Raises:
            requests.exceptions.RequestException: If the HTTP request fails.
        """
        # download time series export
        headers = {"Authorization": f"Bearer {self.token}"}

        # Construct the full URL with filters, top, and skip parameters
        url = f"{self.iot_config['iot_endpoints']['cold_store_download']}/v1/DownloadData('{request_id}')"

        response = requests.get(url, headers=headers, timeout=self.timeout)

        # Raise an exception if the request failed
        if response.status_code != 200:
            response.raise_for_status()

        return response.content
