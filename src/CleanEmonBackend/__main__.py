import argparse

parser = argparse.ArgumentParser(prog="CleanEmonBackend", description="The CLI for CleanEmon-Backend")
subparsers = parser.add_subparsers(help="commands")

# Service
service_parser = subparsers.add_parser("service", help="Run a service")
service_parser.add_argument("service_name", action="store", choices=["api", "disaggregate"])

# Script
script_parser = subparsers.add_parser("script", help="Run a script")
script_parser.add_argument("script_name", action="store", choices=["disaggregate"])
script_parser.add_argument("dates", nargs="*",
                           help="list of dates (YYYY-MM-DD) to be used in `disaggregate` or `reset`")
script_parser.add_argument("--no-safe", action="store_false", default=False,
                           help="prompt before proceeding with critical actions")

# Setup
setup_parser = subparsers.add_parser("setup", help="Setup the backend system")
setup_parser.add_argument("setup_name", action="store", choices=["nilm"])
args = parser.parse_args()

if "service_name" in args:
    if args.service_name == "api":
        from .API.service import run
        run()
    elif args.service_name == "disaggregate":
        from .Disaggregator.service import run
        run()

elif "script_name" in args:
    if args.script_name == "disaggregate":
        from CleanEmonBackend.scripts.disaggregate import disaggregate
        if args.dates:
            disaggregate(*args.dates, no_prompt=args.no_safe)
        else:
            print("You should provide at least one date")

elif "setup_name" in args:
    if args.setup_name == "nilm":
        from . import NILM_CONFIG
        from CleanEmonBackend.scripts.setup import generate_nilm_inference_apis_config

        generate_nilm_inference_apis_config(NILM_CONFIG)
