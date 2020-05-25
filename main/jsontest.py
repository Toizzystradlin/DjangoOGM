
import json

data1 = {
    "doers": [2, 3]
}
data2 = {
    "president": {
        "name": "Zaphod Beeblebrox",
        "species": "Betelgeusian"
    }
}

json_string = json.dumps(data1)

print(json_string[doers])
data = json.loads(json_string)
print(type(data))


