import requests

from modules.base_class import BaseAPIWrapper
from modules.util.config import get_config_by_id, get_system_by_type


class ExternalSystemAPIWrapper(BaseAPIWrapper):
    def __init__(self, config_id: str):
        self.config = get_config_by_id(config_id)
        self.acf_config = get_system_by_type(self.config, "ACF")
        self.path = "/ain/services/api/v1"
        super().__init__(
            self.acf_config["credentials"]["client_id"],
            self.acf_config["credentials"]["client_secret"],
            self.acf_config["credentials"]["token_url"],
            self.acf_config["host"],
        )

    def get_system_id_by_name(self, system_name: str):
        """
        Retrieve the system ID by system name.

        Args:
            system_name (str): The name of the system to search for.

        Returns:
            str: The ID of the system with the specified name.

        Raises:
            requests.exceptions.HTTPError: If the HTTP request returned an unsuccessful status code.
            KeyError: If the expected keys are not found in the response JSON.
        """
        # get all equipments
        headers = {"Authorization": f"Bearer {self.token}"}
        # Construct the full URL with filters, top, and skip parameters
        url = f"{self.base_url}{self.path}/external/systems?$filter=SystemName eq '{system_name}'"

        # Make the request to the endpoint
        response = requests.get(url, headers=headers, timeout=self.timeout)

        # Raise an exception if the request failed
        if response.status_code != 200:
            response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        return data["Systems"][0]["ID"]

    def get_system_ids(self):
        """
        Retrieves the IDs of all external systems.

        This method sends a GET request to the external systems endpoint using the
        provided authorization token and base URL. It parses the JSON response to
        extract and return the list of system IDs.

        Returns:
            list: A list of system IDs.

        Raises:
            requests.exceptions.HTTPError: If the request to the external systems
            endpoint fails with a status code other than 200.
        """
        # get all equipments
        headers = {"Authorization": f"Bearer {self.token}"}
        # Construct the full URL with filters, top, and skip parameters
        url = f"{self.base_url}{self.path}/external/systems"

        # Make the request to the endpoint
        response = requests.get(url, headers=headers, timeout=self.timeout)

        # Raise an exception if the request failed
        if response.status_code != 200:
            response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        return data["Systems"]

    def get_all_external_systems(self, filter_query, top=5000, skip=0):
        """
        Fetch all external systems using pagination until no more data is returned.

        Parameters:
        - filter_query: The ODATA $filter query as a string.
        - top: The batch size for each request (default: 5000).
        - skip: The initial skip value (default: 0).

        Returns:
        - A list of all external systems fetched from the API.
        """
        all_external_systems = []
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        while True:
            # Construct the full URL with filters, top, and skip parameters
            url = f"{self.base_url}{self.path}/externaldata?$filter={filter_query}&$top={top}&$skip={skip}"

            # url = f"{self.base_url}/externaldata"
            # Make the request to the endpoint
            response = requests.get(url, headers=headers, timeout=self.timeout)

            # Raise an exception if the request failed
            if response.status_code != 200:
                response.raise_for_status()

            # Parse the JSON response
            data = response.json()

            # Check if data is returned
            if not data or len(data) == 0:
                break  # Exit loop if no more data is returned

            # Add the returned data to the main list
            all_external_systems.extend(data)

            # Increment the skip parameter for the next batch
            skip += top

        return all_external_systems
