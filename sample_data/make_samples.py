"""Temporary helper: create sample briefs from the valid one."""

import copy
import json
from pathlib import Path

folder = Path("sample_data")

with open(folder / "valid_brief.json", encoding="utf-8") as file:
    valid = json.load(file)


def save(name, brief):
    """Write a brief to sample_data/<name>."""
    with open(folder / name, "w", encoding="utf-8") as file:
        json.dump(brief, file, indent=2, ensure_ascii=False)
        file.write("\n")
    print("created", name)


# 1. The last section is missing
brief = copy.deepcopy(valid)
brief["sections"].pop()
save("missing_section.json", brief)

# 2. One wrong heading
brief = copy.deepcopy(valid)
brief["sections"][2]["heading"] = "Output Spec"
save("wrong_heading.json", brief)

# 3. A field with the wrong type
brief = copy.deepcopy(valid)
brief["sections"][3]["content"]["assumptions"] = "All dates use one time zone."
save("bad_type.json", brief)

# 4. An extra, unexpected field
brief = copy.deepcopy(valid)
brief["sections"][0]["content"]["notes"] = "Added by the author."
save("extra_fields.json", brief)