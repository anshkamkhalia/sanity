import json

def write_json(filename, responses):
    with open(filename,"w") as f:
            json.dump(responses, f, indent=4)
    
