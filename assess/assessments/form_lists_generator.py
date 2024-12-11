import json
import os
from pprint import pprint


def __gather_lists(directory, language_code):
    all_lists = {}
    for filename in os.listdir(directory):
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(directory, filename), "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data.get("lists", []):
                name = item.get("name").strip()
                all_lists.setdefault(name, {"EN": [], "CY": []})[language_code].extend(
                    [{"value": item.get("value").strip()} for item in item.get("items", [])]
                )
    return all_lists


def __combine_rounds(rounds):
    round_lists = {}
    for r in rounds:
        for lang_code, sub_dir in [("EN", "en"), ("CY", "cy")]:
            path = os.path.join(r, sub_dir)
            lists = __gather_lists(path, lang_code)
            for name, items in lists.items():
                round_lists.setdefault(name, {"EN": [], "CY": []})[lang_code].extend(items[lang_code])
    return round_lists


def __extract_translations(round_lists):
    translation_dict, duplicates = {}, set()
    for content in round_lists.values():
        for welsh, english in zip(content["CY"], content["EN"], strict=False):
            welsh_value, english_value = (
                welsh["value"].strip(),
                english["value"].strip(),
            )
            if welsh_value in translation_dict and translation_dict[welsh_value] != english_value:
                duplicates.add(welsh_value)
            translation_dict[welsh_value] = english_value
    return translation_dict, duplicates


# This script is used to dynamically crawl all the form jsons of existing rounds that have both English and Welsh.
# Take the English form and take the Welsh form and create a dictionary of a mapping of the Welsh to English for all
# the list items inside the forms. The list items represent checkbox/radio values. Therefore, we use this mapping that
# is generated to translate things in assessment as it's only an English service.
if __name__ == "__main__":
    # relative path to this current module, will need update if this file is moved
    root_dir = "../../../../digital-form-builder/fsd_config/form_jsons"

    rounds = []
    for dirpath, dirnames, _ in os.walk(root_dir):
        print(dirpath)
        lower_dirnames = [d.lower() for d in dirnames]
        if "en" in lower_dirnames and "cy" in lower_dirnames:
            rounds.append(dirpath)

    round_lists = __combine_rounds(rounds)
    translation_dict, duplicates = __extract_translations(round_lists)
    if duplicates:
        print("Duplicates found:", duplicates)

    content = f"""_LIST_TRANSLATIONS_GENERATED = {json.dumps(
        translation_dict,
        indent=4,
        ensure_ascii=False,
    )}"""

    lines = content.split("\n")
    processed_lines = [line + " # noqa" if len(line) > 118 else line for line in lines]  # for long lines we noqa
    processed_lines[-2] += ","  # add trailing comma to avoid pre-commit failures
    content = "\n".join(processed_lines)

    with open("form_lists_generated_translations.py", "w", encoding="utf-8") as f:
        f.write(content)
    pprint(translation_dict)
