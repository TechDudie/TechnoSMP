import json

from log import error as E

load_json = lambda name: json.loads(open(f"{name}.json", encoding='UTF-8').read())

def save_json(name: str, data: dict):
    with open(f"{name}.json", "w") as file:
        json.dump(data, file, indent=4)

def get_config(context: str) -> dict:
    try:
        return load_json("config")[context]
    except KeyError:
        E("J/Provided configuration context not found")

def get_data() -> dict:
    return load_json("data")

def save_data(data: dict):
    save_json("data", data)