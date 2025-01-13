from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from modules.util.api import APIException
from modules.util.config import get_config_by_id

# ---------------------------------------------------------------------------------------------------------------------------- #


def generate_yearly_slices(start_date_param, end_date_param):
    start_date_formated = datetime.strptime(start_date_param, "%Y-%m-%d")
    end_date_formated = datetime.strptime(end_date_param, "%Y-%m-%d")

    slices = []

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
            lambda x: None
            if pd.isnull(x) or x in ["", "None", np.nan, "nan"]
            else str(x)
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
    df_normal = pd.json_normalize(df_explode[id_explode], sep=sep)
    df_normal.columns = [f"{id_explode}{sep}{col}" for col in df_normal.columns]

    # step 3: concatenate the IDs and normalized data into a single data frame
    df_final = pd.concat([df_explode[id], df_normal], axis=1)
    return df_final


# ---------------------------------------------------------------------------------------------------------------------------- #


class Logger:
    _loggers = {}
    _format = "%(asctime)s [%(levelname)s]:\t%(message)s"

    @staticmethod
    def get_logger(config_id: str):
        if config_id in Logger._loggers:
            return Logger._loggers[config_id]

        log_config = get_config_by_id(config_id).get("log")

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
        logger = Logger.get_logger(config_id)
        log_file = logger.handlers[0].baseFilename
        with open(log_file, "w"):
            pass

    @staticmethod
    def blank_line(logger, count=1):

        for handler in logger.handlers:
            handler.setFormatter(logging.Formatter(""))

        for _ in range(count):
            logger.info("")

        for handler in logger.handlers:
            handler.setFormatter(logging.Formatter(Logger._format))


# class Logger:
#     """
#     A custom logger class that sets up logging to both a file and the console.
#     Attributes:
#         logger (logging.Logger): The logger instance.
#     Methods:
#         __init__(name: str, log_file: str, level: int = logging.INFO):
#             Initializes the Logger with the specified name, log file, and logging level.
#         get_logger():
#             Returns the logger instance.
#     """

#     def __init__(
#         self, name: str, log_file: str, level: int = logging.INFO, print: bool = False
#     ):
#         """
#         Initializes a logger instance with a specified name, log file, and logging level.
#         Args:
#             name (str): The name of the logger.
#             log_file (str): The file path where the log messages will be saved.
#             level (int, optional): The logging level. Defaults to logging.INFO.
#         Attributes:
#             logger (logging.Logger): The logger instance.
#         """

#         self.logger = logging.getLogger(name)
#         self.logger.setLevel(level)
#         self.formatter = logging.Formatter("%(asctime)s [%(levelname)s]:\t%(message)s")

#         # Clear existing handlers
#         if self.logger.hasHandlers():
#             self.logger.handlers.clear()

#         # create a file handler
#         if not os.path.exists(log_file):
#             with open(log_file, "a"):
#                 pass

#         file_handler = logging.FileHandler(log_file)
#         file_handler.setLevel(level)
#         file_handler.setFormatter(self.formatter)
#         self.logger.addHandler(file_handler)

#         if print:
#             console_handler = logging.StreamHandler()
#             console_handler.setLevel(level)
#             console_handler.setFormatter(self.formatter)
#             self.logger.addHandler(console_handler)

#     def get_logger(self):
#         return self.logger

#     def clear_log_file(self):
#         """
#         Clears the log file by truncating its content.
#         """
#         log_file = self.logger.handlers[0].baseFilename
#         with open(log_file, "w"):
#             pass
