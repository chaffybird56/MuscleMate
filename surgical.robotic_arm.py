"""
Legacy entrypoint retained for backwards compatibility.

Prefer using the package entry point via ``python -m musclemate.cli``.
"""

from musclemate.cli import main


if __name__ == "__main__":
    raise SystemExit(main())

