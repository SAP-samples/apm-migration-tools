import os
import yaml


class EquipmentMappingCache:
    """
    A class to manage the equipment mapping cache.
    """

    _cache = None

    @classmethod
    def load(cls):
        """
        Load the equipment mapping file and cache its content.
        Returns:
            dict: The content of the equipment mapping file.
        """
        if cls._cache is None:
            filepath = os.path.join("custom", "equipment_mapping.yaml")
            print(f"Reading equipment mapping file: {filepath}")
            with open(filepath, "r", encoding="utf-8") as file:
                cls._cache = yaml.safe_load(file)
        return cls._cache


def load_equipment_mapping():
    """
    Load the equipment mapping file and cache its content.
    Returns:
        dict: The content of the equipment mapping file.
    """
    return EquipmentMappingCache.load()


def equipment_mapper(equipment_id: str) -> str:
    """
    Check if there is a mapping for the given equipment ID and return the mapped ID.
    If no mapping is found, return the original equipment ID.
    Args:
        equipment_id (str): The equipment ID to be mapped.
    Returns:
        str: The mapped equipment ID.
    """
    # Lade die Mapping-Daten (nur beim ersten Aufruf)
    mapping = load_equipment_mapping()

    # Überprüfe, ob die equipment_id im Mapping vorhanden ist
    return mapping.get(equipment_id, equipment_id)
