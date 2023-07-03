import json

load_json = lambda name: json.loads(open(f"{name}.json", encoding='UTF-8').read())

def save_json(name, data):
    with open(f"{name}.json", "w") as file:
        json.dump(data, file, indent=4)

def get_config(context) -> dict:
    return load_json("config")[context]

def get_data() -> dict:
    return load_json("data")

def save_data(data: dict):
    save_json("data", data)