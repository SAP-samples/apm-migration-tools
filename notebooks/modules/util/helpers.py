# standard imports
import logging
import os
from datetime import datetime, timedelta
import pandas as pd
import pyarrow as pa
import numpy as np

# custom imports
from modules.util.config import get_config_by_id


def generate_slices(start_date_param, end_date_param, interval="YEARS"):
    """
    Generate slices based on the start and end date parameters
    Parameters:
        start_date_param(str): Start date parameter
        end_date_param(str): End date parameter
        interval(str, optional): Interval for slicing. **Defaults to year**
    Returns:
        list: List of tuples containing start and end date for each slice
    """
    start_date_formated = datetime.strptime(start_date_param, "%Y-%m-%d")
    end_date_formated = datetime.strptime(end_date_param, "%Y-%m-%d")

    slices = []

    if interval == "YEARS":
        if start_date_formated.year == end_date_formated.year:
            start_date = datetime(start_date_formated.year, 1, 1)
            end_date = datetime(end_date_formated.year, 12, 31)
            slices.append((start_date, end_date))
        else:
            # Adjust the first interval if the start date is not January 1st
            if start_date_formated.month != 1 or start_date_formated.day != 1:
                first_end_date = datetime(start_date_formated.year, 12, 31)
                slices.append((start_date_formated, first_end_date))
                start_date_formated = first_end_date + timedelta(days=1)

            # Adjust the last interval if the end date is not December 31st
            if end_date_formated.month != 12 or end_date_formated.day != 31:
                last_start_date = datetime(end_date_formated.year, 1, 1)
                slices.append((last_start_date, end_date_formated))
                end_date_formated = last_start_date - timedelta(days=1)

            # Generate full year intervals
            current_start_date = start_date_formated
            while current_start_date <= end_date_formated:
                current_end_date = datetime(current_start_date.year, 12, 31)
                slices.append((current_start_date, current_end_date))
                current_start_date = datetime(current_start_date.year + 1, 1, 1)

    elif interval == "MONTHS":
        current_start_date = start_date_formated
        while current_start_date <= end_date_formated:
            current_end_date = (
                datetime(current_start_date.year, current_start_date.month, 1)
                + timedelta(days=32)
            ).replace(day=1) - timedelta(days=1)
            if current_end_date > end_date_formated:
                current_end_date = end_date_formated
            slices.append((current_start_date, current_end_date))
            current_start_date = current_end_date + timedelta(days=1)

    elif interval == "WEEKS":
        current_start_date = start_date_formated
        while current_start_date <= end_date_formated:
            current_end_date = current_start_date + timedelta(days=6)
            if current_end_date > end_date_formated:
                current_end_date = end_date_formated
            slices.append((current_start_date, current_end_date))
            current_start_date = current_end_date + timedelta(days=1)

    elif interval == "DAYS":
        current_start_date = start_date_formated
        while current_start_date <= end_date_formated:
            current_end_date = current_start_date
            slices.append((current_start_date, current_end_date))
            current_start_date = current_end_date + timedelta(days=1)

    return slices


def convert_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts a dataframe content to string datatype. If there are any blank lists or values,
    they are replaced with NULL during the conversion.
    Parameters:
        df: Source dataframe
    Returns:
        pandas.DataFrame: converted dataframe
    """

    # Replace empty lists with None
    df = df.apply(
        lambda col: col.map(lambda x: None if isinstance(x, list) and not x else x)
    )
    df = df.astype(str)
    # Replace NaN or specific empty values with None, and convert to string
    df = df.apply(
        lambda col: col.map(
            lambda x: (
                None if pd.isnull(x) or x in ["", "None", np.nan, "nan"] else str(x)
            )
        )
    )
    return df


def explode_normalize(data: pd.DataFrame, id: list, id_explode: str, sep: str = "_"):
    """
    Explode and normalize data in a Data Frame

    Parameters:
        data(pandas.DataFrame): Dataframe that contains the data
        id(list): List of IDs which would be retained in the dataframe - usually key fields
        id_explode(str): Column ID based on which data needs to be exploded
        sep(str, optional): Seperator based on which the exploded column names are derived. **Defaults to underscore(_)**
    """

    # step 1: pick relevant fields from the dataframe (id fields, exploded field) and explode
    df_explode = data[id + [id_explode]]
    df_explode = df_explode.explode(id_explode).reset_index(drop=True)

    # step 2: normalize the exploded field and rename it as exploded{sep}field for identification
    df_normal = pd.json_normalize(df_explode[id_explode].tolist(), sep=sep)
    df_normal.columns = [f"{id_explode}{sep}{col}" for col in df_normal.columns]

    # step 3: concatenate the IDs and normalized data into a single data frame
    df_final = pd.concat([df_explode[id], df_normal], axis=1)
    return df_final


def convert_unix_to_iso(time: int) -> str:
    """
    Converts Unix timestamp in milliseconds to ISO format

    Parameters:
        unix_time(int): Unix timestamp
    Returns:
        str: ISO formatted date -> 2024-08-01T00:01:00.010Z
    """
    return (
        datetime.utcfromtimestamp(time / 1000).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        + "Z"
    )


# ------------------------------------------------------------------------------------ #


class Logger:
    """
    Logger class provides methods to create and manage loggers with specific configurations.
    Attributes:
        _loggers (dict): A dictionary to store loggers by their configuration ID.
        _format (str): The format string for log messages.
    Methods:
        get_logger(config_id: str) -> logging.Logger:
            Retrieves a logger based on the given configuration ID. If the logger does not exist, it creates one using the configuration.
        clear_log_file(config_id: str):
            Clears the log file associated with the given configuration ID.
        blank_line(logger: logging.Logger, count: int = 1):
            Inserts a specified number of blank lines into the log.
    """

    _loggers = {}
    _format = "%(asctime)s  [%(levelname).4s]: %(message)s"

    @staticmethod
    def get_logger(config_id: str):
        """
        Retrieves or creates a logger based on the provided configuration ID.
        If a logger with the specified configuration ID already exists, it is returned.
        Otherwise, a new logger is created using the configuration associated with the ID.
        Args:
            config_id (str): The ID of the configuration to use for the logger.
        Returns:
            logging.Logger: The configured logger instance.
        Raises:
            ValueError: If no configuration is found for the provided ID or if the log configuration is missing.
        Configuration:
            The configuration should include the following keys:
            - "log": A dictionary with the following keys:
                - "name" (optional): The name of the logger. Defaults to the config_id if not provided.
                - "directory": The directory where the log file will be stored.
                - "level": The logging level (e.g., logging.DEBUG, logging.INFO).
                - "print": A boolean indicating whether to also print logs to the console.
        """

        if config_id in Logger._loggers:
            return Logger._loggers[config_id]

        config = get_config_by_id(config_id)
        if config is None:
            raise ValueError(f"No configuration found for ID: {config_id}")
        log_config = config.get("log")
        if log_config is None:
            raise ValueError(f"No log configuration found for ID: {config_id}")

        name = log_config.get("name") or config_id
        file = f"{log_config.get('directory')}/{name}.log"
        level = log_config.get("level")
        print_log = log_config.get("print")
        formatter = logging.Formatter(Logger._format)

        logger = logging.getLogger(name)
        logger.setLevel(level)

        if logger.hasHandlers():
            logger.handlers.clear()

        if not os.path.exists(file):
            with open(file, "a"):
                pass

        file_handler = logging.FileHandler(file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        if print_log:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        Logger._loggers[config_id] = logger
        return logger

    @staticmethod
    def clear_log_file(config_id: str):
        """
        Clears the log file associated with the given configuration ID.
        This function retrieves the logger associated with the provided configuration ID,
        identifies the log file used by the logger, and clears its contents.
        Args:
            config_id (str): The configuration ID used to retrieve the appropriate logger.
        Raises:
            StopIteration: If no FileHandler is found in the logger's handlers.
        """

        logger = Logger.get_logger(config_id)
        log_file = next(
            handler.baseFilename
            for handler in logger.handlers
            if isinstance(handler, logging.FileHandler)
        )
        with open(log_file, "w", encoding="utf-8"):
            pass

    @staticmethod
    def blank_line(logger, count=1):
        """
        Inserts blank lines into the logger output.
        This function temporarily removes the formatter from the logger handlers,
        logs the specified number of blank lines, and then restores the original formatter.
        Args:
            logger (logging.Logger): The logger instance to which blank lines will be added.
            count (int, optional): The number of blank lines to insert. Defaults to 1.
        """

        for handler in logger.handlers:
            handler.setFormatter(logging.Formatter(""))

        for _ in range(count):
            logger.info("")

        for handler in logger.handlers:
            handler.setFormatter(logging.Formatter(Logger._format))


def get_parquet_schema(
    df: pd.DataFrame, indicator_mapping: dict, log: Logger
) -> pa.Schema:
    """
    Generates a schema from a dataframe

    Parameters:
        data(pandas.DataFrame): Dataframe for which schema needs to be generated
    Returns:
        pyarrow.Schema: Schema generated from the dataframe
    """

    # schema = pa.Schema.from_pandas(data)
    res_schema = pa.schema([])
    res_schema = res_schema.append(pa.field("managedObjectId", pa.string()))
    res_schema = res_schema.append(pa.field("measuringNodeId", pa.string()))
    res_schema = res_schema.append(pa.field("_time", pa.timestamp("ms")))

    for column in df.columns:
        if column in res_schema.names:
            continue
        for char_details in indicator_mapping.values():
            if char_details is None:
                continue
            if column == f"C_{char_details.characteristicsInternalId}":
                if column in res_schema.names:
                    continue
                if char_details.dataType == "NUM":
                    res_schema = res_schema.append(pa.field(column, pa.float64()))

                    # if char_details.charcDecimals == 0:
                    #     # res_schema = res_schema.append(pa.field(column, pa.int64()))
                    #     res_schema = res_schema.append(pa.field(column, pa.float64()))
                    #     # convert float values to int64
                    #     df[column] = (
                    #         df[column]
                    #         .apply(
                    #             lambda x: (
                    #                 int(x) if pd.notna(x) and np.isfinite(x) else x
                    #             )
                    #         )
                    #         .astype("Int64")
                    #     )
                    # else:
                    #     res_schema = res_schema.append(pa.field(column, pa.float64()))
                elif char_details.dataType == "DATE":
                    df[column] = df[column].astype("datetime64[ms]")
                    res_schema = res_schema.append(pa.field(column, pa.date64()))
                else:
                    log.error(f"Unknown data type {char_details.dataType}")

    return res_schema
