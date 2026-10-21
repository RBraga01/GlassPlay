"""Nevermore entry point."""

from raven_framework.core.run_app import RunApp

from nevermore import NevermoreApp


if __name__ == "__main__":
    import sys
    if "--reset-discoveries" in sys.argv:
        from nevermore.discoveries import Discoveries
        Discoveries().reset()
        print("Nevermore discoveries reset.")
        raise SystemExit(0)
    RunApp.run(
        lambda: NevermoreApp(),
        app_id="",
        app_key="",
    )
