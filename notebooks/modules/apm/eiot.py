from modules.util.api import APMClient, APIException
from modules.util.helpers import Logger
from typing import TypedDict, List


def get_apm_type(to_type: str) -> str:
    """
    Get the APM type for the given TO type
    """
    if to_type == "EQU":
        return "EQUI"
    else:
        return to_type


class Indicator(TypedDict):
    # Define the structure of the indicators if known
    modifiedAt: str
    indicatorId: str
    categoryName: str
    characteristicsInternalId: str
    positionDetailsId: str
    dataType: str
    unitOfMeasure: str
    charcLength: int
    charcDecimals: int
    syncStatus: str
    syncStartTime: str
    syncEndTime: str
    syncMessage: str
    eIotSyncTime: str
    measuringNodeId: str
    technicalGroupId: str
    c8yManagedObjectId: str


class EIoTSyncStatus(TypedDict):
    number: str
    SSID: str
    type: str
    managedObjectId: str
    syncStartTime: str
    syncEndTime: str
    eIotSyncTime: str
    syncMessage: str
    technicalObjectSyncStatus: str
    indicators: List[Indicator]


class EIoTFileUploadResponse(TypedDict):
    fileId: str
    fileName: str
    uploadedTime: str


class EIoTFileUploadStatusResponse(TypedDict):
    fileId: str
    fileName: str
    fileSize: int
    numberOfRecords: int
    uploadedTime: str
    status: str
    description: str
    processingEndTime: str


class EIoTApi:
    """
    SAP API Documentation:
    - https://api.sap.com/api/EmbeddedIoTMetadataSync_APIs/overview
    - https://api.sap.com/api/FileUploader_APIs/resource/FileUpload
    """

    def __init__(self, config_id: str):
        """
        Initializes the class object with necessary variables and utility module objects
        """
        self.api_metadata = APMClient(
            config_id=config_id, service="/EIoTMetadataSyncService/v1"
        )
        self.api_file = APMClient(config_id=config_id, service="/FileUploadService/v1")
        self.log = Logger.get_logger(config_id)

    def get_eiot_sync_status_by_to(
        self, number: str, ssid: str, to_type: str
    ) -> EIoTSyncStatus:
        """
        Get the status of the EIoT Metadata Sync
        """
        headers = {
            "x-api-key": self.api_metadata.x_api_key,
        }

        endpoint_suffix = (
            f"/TechnicalObjects(number='{number}',"
            f"SSID='{ssid}',type='{get_apm_type(to_type)}')?$expand=indicators"
        )

        api_url = f"{self.api_metadata.base_url}{endpoint_suffix}"

        response = self.api_metadata.get(api_url, headers=headers)
        data: EIoTSyncStatus = response.json()
        return data

    def get_ssid(self) -> str:
        """
        Get the SSID of any technical object
        """
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_metadata.x_api_key,
        }

        endpoint_suffix = "/TechnicalObjects?$top=1&$select=SSID"

        api_url = f"{self.api_metadata.base_url}{endpoint_suffix}"

        response = self.api_metadata.get(api_url, headers=headers)
        data: EIoTSyncStatus = response.json()
        return data["value"][0]["SSID"]

    def upload_file(self, parquet_file_and_path: str):
        """
        Upload a file to the API
        """
        headers = {
            "accept": "application/json",
            "x-api-key": self.api_file.x_api_key,
        }

        endpoint_suffix = "/upload"

        api_url = f"{self.api_file.base_url}{endpoint_suffix}"

        with open(parquet_file_and_path, "rb") as file:
            # Create a dictionary with the file data
            # we need to extract the file name from the path
            file_name = parquet_file_and_path.split("/")[-1]
            files = {"file": (file_name, file, "application/octet-stream")}

            response = self.api_file.post(
                api_url,
                headers=headers,
                files=files,
            )
            if response.status_code == 202:
                data: EIoTFileUploadResponse = response.json()
                return data
            else:
                raise APIException(
                    endpoint=api_url,
                    status_code=response.status_code,
                    response=response,
                )

    def get_file_status(self, file_id: str) -> bool:
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_file.x_api_key,
        }

        endpoint_suffix = f"/files/status('{file_id}')"

        api_url = f"{self.api_file.base_url}{endpoint_suffix}"

        response = self.api_file.get(api_url, headers=headers)
        data: EIoTFileUploadStatusResponse = response.json()
        return data
