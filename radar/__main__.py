"""CLI:  python -m radar update [--only workday:dyson]   fetch, merge, export the site
        python -m radar export                          rebuild site files from the store
        python -m radar reclassify                      re-apply classify.py rules to stored jobs
        python -m radar digest [--no-draft]             write this week's digest (and Buttondown draft)
        python -m radar health                          list failing sources
"""
import json
import sys

from . import digest, export, pipeline


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "update"
    if cmd == "update":
        only = argv[argv.index("--only") + 1] if "--only" in argv else None
        print(json.dumps(pipeline.update(only=only)))
        print(json.dumps(export.write_site()))
    elif cmd == "export":
        print(json.dumps(export.write_site()))
    elif cmd == "reclassify":
        print(json.dumps(pipeline.reclassify()))
        print(json.dumps(export.write_site()))
    elif cmd == "digest":
        print(json.dumps(digest.run(send_draft="--no-draft" not in argv)))
    elif cmd == "health":
        bad = {k: v for k, v in pipeline.load_store()["sources"].items() if not v["ok"]}
        print(json.dumps(bad, indent=1) if bad else "all sources ok")
        return 1 if bad else 0
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
