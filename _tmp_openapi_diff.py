import json, difflib

old = json.load(open("openapi.json"))
new = json.load(open("openapi.new.json"))
if old != new:
    print("OPENAPI DIFF:")
    for line in difflib.unified_diff(
        json.dumps(old, indent=2).splitlines(),
        json.dumps(new, indent=2).splitlines(),
        fromfile="openapi.json",
        tofile="openapi.new.json",
    ):
        print(line)
else:
    print("OPENAPI: no diff")
