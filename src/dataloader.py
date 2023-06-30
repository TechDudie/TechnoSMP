import json

load_json = lambda name: json.loads(open(f"{name}.json", encoding='UTF-8').read())