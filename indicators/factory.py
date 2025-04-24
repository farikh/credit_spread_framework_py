import importlib
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text


def get_indicator_class(short_name: str):
    """
    Retrieves the indicator class and its full metadata for a given short name.
    Returns: (indicator_class, metadata_dict)
    """
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT * FROM indicators WHERE ShortName = :sn AND IsActive = 1"),
            {"sn": short_name}
        ).mappings().fetchone()

    if result is None:
        raise ValueError(f"[ERROR] Indicator '{short_name}' not found or inactive in database.")

    metadata = dict(result)
    class_path = metadata["ClassPath"]
    module_path, class_name = class_path.rsplit(".", 1)

    try:
        module = importlib.import_module(module_path)
        indicator_class = getattr(module, class_name)
    except Exception as e:
        raise ImportError(f"[ERROR] Failed to load '{class_path}': {e}")

    return indicator_class, metadata


def get_all_indicator_classes():
    """
    Retrieves all active indicator classes from the database.
    Returns: { ShortName: (indicator_class, metadata_dict) }
    """
    engine = get_engine()
    with engine.begin() as conn:
        results = conn.execute(
            text("SELECT * FROM indicators WHERE IsActive = 1")
        ).mappings().fetchall()

    indicator_classes = {}

    for row in results:
        metadata = dict(row)
        short_name = metadata["ShortName"]
        class_path = metadata["ClassPath"]

        try:
            module_path, class_name = class_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            indicator_class = getattr(module, class_name)
            indicator_classes[short_name] = (indicator_class, metadata)
        except Exception as e:
            print(f"[WARNING] Failed to load indicator '{short_name}' from '{class_path}': {e}")

    return indicator_classes
