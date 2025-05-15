import csv
from state import GlobalState
import os

def load_references():
    """
    Загружает справочники из файла reference_items.csv в виде словаря {название: значение}.
    """
    GlobalState.references = {}  # Очищаем сначала

    if not GlobalState.current_workspace_path:
        return

    references_path = os.path.join(GlobalState.current_workspace_path, "reference_items.csv")
    if not os.path.exists(references_path):
        return

    try:
        with open(references_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row.get('Название', '').strip()
                value = row.get('Значение', '').strip()
                if key:
                    GlobalState.references[key] = value
    except Exception as e:
        print(f"Ошибка загрузки справочников: {e}")
