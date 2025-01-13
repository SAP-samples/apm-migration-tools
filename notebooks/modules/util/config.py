import os
import yaml
from jsonschema import Draft202012Validator
from dotenv import dotenv_values

CONFIG_PATH = "../config"


def read_config_files(directory, target_config_id):
    # load the schema
    schema_filepath = os.path.join(directory, "__config__schema.json")
    with open(schema_filepath, "r", encoding="utf-8") as file:
        schema = yaml.safe_load(file)

    def replace_placeholders(obj, env_vars):
        if isinstance(obj, dict):
            return {k: replace_placeholders(v, env_vars) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_placeholders(i, env_vars) for i in obj]
        elif isinstance(obj, str):
            for key, value in env_vars.items():
                obj = obj.replace(f"${key}", value)
            return obj
        else:
            return obj

    for filename in os.listdir(directory):
        if filename.endswith(".yaml"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r", encoding="utf-8") as file:
                content = yaml.safe_load(file)
                if content.get("config_id") == target_config_id:
                    Draft202012Validator(schema=schema).validate(content)

                    env_vars = dotenv_values(os.path.join(CONFIG_PATH, ".env"))
                    content = replace_placeholders(content, env_vars)

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


def get_config_global():
    schema_file = "__config_global_schema.json"
    content_file = "__config_global.yaml"

    # load the schema
    schema_filepath = os.path.join(CONFIG_PATH, schema_file)
    with open(schema_filepath, "r", encoding="utf-8") as file:
        schema = yaml.safe_load(file)

    # load the content
    config_filepath = os.path.join(CONFIG_PATH, content_file)
    with open(config_filepath, "r", encoding="utf-8") as file:
        content = yaml.safe_load(file)
        Draft202012Validator(schema=schema).validate(content)
        return content
    return None
