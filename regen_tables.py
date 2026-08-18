#!/usr/bin/env python3
"""Compatibility entry point for the sole verified manuscript generator.

The full fail-closed implementation lives in :mod:`analyze_main_results`.  Keep
this filename as a convenient command and as compatibility with the recovery
commit that introduced it, but do not maintain a second calculation path.

Running ``python regen_tables.py`` therefore regenerates exactly the same
30-design tables, claim ledger, and figures as ``python analyze_main_results.py``.
All command-line options, including ``--check`` and ``--no-figures``, are passed
through unchanged because ``analyze_main_results.main`` parses ``sys.argv``.
"""

from analyze_main_results import main


if __name__ == "__main__":
    raise SystemExit(main())
