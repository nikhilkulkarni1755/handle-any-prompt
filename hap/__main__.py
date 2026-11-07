import argparse
import logging
import sys

from hap.apple_fm import AppleFMBackend
from hap.pipeline import ingest
from hap.store import Store
from hap.summary import render


def main() -> None:
    ap = argparse.ArgumentParser(prog="hap", description="Summarize a prompt of any size without losing detail.")
    ap.add_argument("file", nargs="?", default="-", help="prompt file, or - for stdin")
    ap.add_argument("-o", "--out", help="write the summary here instead of stdout")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)

    text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
    backend, store = AppleFMBackend(), Store()
    try:
        summary = render(store, ingest(text, store, backend))
    finally:
        backend.close()
    if args.out:
        open(args.out, "w", encoding="utf-8").write(summary)
    else:
        print(summary)


main()
