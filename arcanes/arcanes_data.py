ARCANE_DISSOLUTION_PATH = "C:\\Users\\adipe\\PycharmProjects\\Warframe-Market-Tool\\arcanes\\data\\dissolution.txt"
ARCANE_COLLECTIONS_PATH = "C:\\Users\\adipe\\PycharmProjects\\Warframe-Market-Tool\\arcanes\\data\\collections.txt"

COUNT_FOR_RANK = [1, 3, 6, 10, 15, 21]

def get_arcane_dissolution():
    with open(ARCANE_DISSOLUTION_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    arcanes_data = content.split("[")
    arcanes_dissolution = {}
    for data in arcanes_data:
        data = data[1:].split("\"", 1)
        name = data[0].strip()
        dissolution_index = data[1].lower().find("dissolution")
        dissolution = data[1][dissolution_index + len("dissolution"):].split("=",1)[1].split(",",1)[0].strip()
        if dissolution == "false":
            arcanes_dissolution[name] = None
        else:
            arcanes_dissolution[name] = int(dissolution)

    return arcanes_dissolution


def get_arcane_collections():
    with open(ARCANE_COLLECTIONS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    collections_data = content.split("!")[1:]
    arcanes_collections = {}
    for data in collections_data:
        data = data.split(":")
        name = data[0].strip()
        items = data[1].strip().split("\n")

        collection = {}
        probs = []
        rarity_counts = {}
        curr_rarity = 0
        for item in items:
            if "%" in item:
                probs.append(float(item.strip().replace("%", "")) / 100.0)
                curr_rarity += 1
            else:
                rarity_counts[curr_rarity] = rarity_counts.get(curr_rarity, 0) + 1
                collection[item.strip()] = curr_rarity

        for arcane in collection:
            rarity = collection[arcane]
            prob = probs[rarity] / rarity_counts[rarity]
            collection[arcane] = prob
        arcanes_collections[name] = collection

    return arcanes_collections