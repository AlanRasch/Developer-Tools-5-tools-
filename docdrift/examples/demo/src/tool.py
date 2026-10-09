"""A tiny command-line tool used to demonstrate docdrift."""

import argparse
import os

DEFAULT_FORMAT = "text"


def load_settings():
    return {"database_url": os.getenv("DATABASE_URL", "sqlite:///local.db")}


def build_report(rows, format_name):
    if format_name == "json":
        return "[" + ",".join(str(r) for r in rows) + "]"
    return "\n".join(str(r) for r in rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", default=DEFAULT_FORMAT)
    parser.add_argument("--output")
    args = parser.parse_args()
    print(build_report([1, 2, 3], args.format))


if __name__ == "__main__":
    main()
