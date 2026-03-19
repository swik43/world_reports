import json


def expand_rages():

    with open("./AI/contents_config.json", "r") as f:
        data = f.read()
        parsed_config = json.loads(data)

    for country in parsed_config:
        contents_range = parsed_config[country]["contents_pages"]
        if len(contents_range) == 1:
            continue
        contents_range[-1] += 1
        full_range = list(range(*contents_range))
        print(full_range)


if __name__ == "__main__":
    expand_rages()
