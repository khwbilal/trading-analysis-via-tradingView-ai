"""python -m app.jobs <job> [--scheduled]: run one job and exit with its code.

Task Scheduler passes --scheduled (register.ps1); a run without it is recorded as manual.
"""

from __future__ import annotations

import sys

from . import JOBS, run_job


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    scheduled = "--scheduled" in args
    args = [a for a in args if a != "--scheduled"]
    if len(args) != 1:
        print(f"usage: python -m app.jobs <job> [--scheduled]   (jobs: {', '.join(sorted(JOBS))})", file=sys.stderr)
        return 2
    return run_job(args[0], "scheduled" if scheduled else "manual")


if __name__ == "__main__":
    sys.exit(main())
