# Demo Tool

Run the tool from the command line:

```bash
python src/tool.py --format json
python src/tool.py --verbose
```

Settings come from the `DATABASE_URL` environment variable.

Load settings with `load_settings()` and build a report with `build_report()`.
The old `render_report()` function prints the report, and `LegacyParser` handles the old format.

See the [design notes](docs/design.md) and the [changelog](CHANGELOG.md).
