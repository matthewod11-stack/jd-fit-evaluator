from __future__ import annotations
from .schema import coerce_to_canonical
import json, sys

def main():
    data = json.load(sys.stdin)
    out = coerce_to_canonical(data)
    sys.stdout.write(out.model_dump_json(indent=2))

if __name__ == "__main__":
    main()