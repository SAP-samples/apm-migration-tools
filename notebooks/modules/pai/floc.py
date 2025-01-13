import requests

from modules.base_class import BaseAPIWrapper
from modules.util.config import get_config_by_id, get_system_by_type


class FlocAPIWrapper(BaseAPIWrapper):
    def __init__(self, config_id: str):
        self.config = get_config_by_id(config_id)
        self.iot_config = get_system_by_type(self.config, "ACF")
        self.path = "/ain/services/api/v1"
        super().__init__(
            self.iot_config["credentials"]["client_id"],
            self.iot_config["credentials"]["client_secret"],
            self.iot_config["credentials"]["token_url"],
            self.iot_config["host"],
        )

    def _get_total_count(self):
        # Get the total count of equipments
        headers = {"Authorization": f"Bearer {self.token}"}
        count_url = f"{self.base_url}{self.path}/floc/$count"
        response = requests.get(count_url, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return int(response.text)

    def get_flocs(self, batch_size=500):
        # get all equipments
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        total_count = self._get_total_count()
        flocs = []

        # ONLY FOR TESTING
        total_count = 500

        for skip in range(0, total_count, batch_size):
            params = {"$top": batch_size, "$skip": skip}
            response = requests.get(
                f"{self.base_url}{self.path}/floc",
                headers=headers,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            flocs.extend(data)

        return flocs

    def get_by_search(
        self,
        filter_query,
        select=None,
        top=1000,
        skip=0,
    ):
        if select is None:
            select = [
                "flocId",
                "internalId",
                "templates",
                "modelId",
                "status",
                "externalSystemId",
                "description",
            ]
        # search for equipments by a given filter query
        headers = {
            "Authorization": f"Bearer {self.token}",
            "content-type": "application/json",
        }
        all_equipments = []
        search_after = ""

        while True:
            # Construct the full URL with filters, top, and skip parameters
            url = f"{self.base_url}{self.path}/search/floc"

            body = {
                "filter": filter_query,
                "top": top,
                "skip": skip,
                "orderBy": {"path": "changedOn", "descending": True, "type": None},
                "select": select,
                "searchAfter": search_after,
            }

            # Make the request to the endpoint
            response = requests.put(
                url, headers=headers, timeout=self.timeout, json=body
            )

            # Raise an exception if the request failed
            if response.status_code != 200:
                response.raise_for_status()

            # Parse the JSON response
            data = response.json()

            # Check if data is returned
            if not data or len(data["value"]) == 0:
                break  # Exit loop if no more data is returned

            # set search_afer
            if "searchAfter" in data:
                search_after = data["searchAfter"]
                # print(f"search_after: {search_after}")

            # iterate over data["value"] and get the equipmentId
            # for each equipment
            for floc in data["value"]:
                if floc["modelId"] is None and len(floc["templates"]) == 0:
                    # print(
                    #     f"No modelId and templates - skip equipmentId: {equipment['equipmentId']} {equipment['description']["short"]}"
                    # )
                    continue
                else:
                    all_equipments.append(floc)

            # print the value of the variable skip every 100000 records
            if skip % 100000 == 0:
                # calculate the percentage of the records fetched
                percentage = (skip / data["count"]) * 100
                print(f"skip: {skip} / total records: {data['count']} -> {percentage}%")

            # Increment the skip parameter for the next batch
            skip += top

            # if len(all_equipments) > 5:
            #     break

        return all_equipments
