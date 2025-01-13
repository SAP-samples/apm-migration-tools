import os
import yaml
from jsonschema import Draft202012Validator

CONFIG_PATH = "../config"


def read_config_files(directory, target_config_id):
    # load the schema
    schema_filepath = os.path.join(directory, "__config__schema.json")
    with open(schema_filepath, "r", encoding="utf-8") as file:
        schema = yaml.safe_load(file)

    for filename in os.listdir(directory):
        if filename.endswith(".yaml"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r", encoding="utf-8") as file:
                content = yaml.safe_load(file)
                if content.get("config_id") == target_config_id:
                    Draft202012Validator(schema=schema).validate(content)
                    return content
    return None


def get_config_by_id(config_id: str):
    """
    Retrieve configuration content by its identifier.

    Args:
        config_id (str): The identifier of the configuration to retrieve.

    Returns:
        dict: The content of the configuration file corresponding to the given identifier.
    """
    config_content = read_config_files(CONFIG_PATH, config_id)
    return config_content


def get_system_by_type(config, system_type: str):
    """
    Retrieve system configuration by its type.

    Args:
        config (dict): The configuration dictionary.
        system_type (str): The type of the system to retrieve.

    Returns:
        dict: The configuration of the system corresponding to the given type.
    """
    for system in config["systems"]:
        if system["type"] == system_type:
            return system
    return None


def get_mapping():
    """
    Retrieves the mapping configuration from a YAML file.
    This function constructs the file path to the "mapping.yaml" file located
    in the directory specified by CONFIG_PATH. If the file exists, it reads
    the file and returns its contents as a dictionary. If the file does not
    exist, it returns None.
    Returns:
        dict or None: The contents of the "mapping.yaml" file as a dictionary
        if the file exists, otherwise None.
    """
    mapping_filepath = os.path.join(CONFIG_PATH, "mapping.yaml")
    if os.path.exists(mapping_filepath):
        with open(mapping_filepath, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    return None
