"""Command-line interface for Tessera AI Indexer.

Installed as the `tessera-indexer` console script by the wheel.

Subcommands:
  check         Smoke-test an install: taxonomy, QR tier, Tier-4 model status
  classify      Classify a single email body (text) and print the routing JSON
  ingest-batch  Process a directory of {email_id}_body.txt + *_attachment.pdf
  version       Print the installed version
"""
import argparse
import json
import sys

from indexer import __version__


def cmd_check(args) -> int:
    from indexer.rules.engine import RuleEngine

    print("Tessera AI Indexer install check")
    print(f"  version:   {__version__}")
    engine = RuleEngine(config=args.config)
    print(f"  taxonomy:  {len(engine.schemas)} schema(s): {', '.join(sorted(engine.schemas))}")
    print(f"  tier1 QR:  {'ok' if engine.tier1 is not None else 'MISSING'}")
    if engine.tier4 is None:
        print("  tier4:     not initialized (see errors above)")
    else:
        backend = "onnx"
        if engine.tier4.onnx_session is None:
            backend = "tfidf" if engine.tier4.tfidf_model is not None else "none"
        print(f"  tier4:     {backend}")
    return 0


def cmd_config(args) -> int:
    from indexer.config import load_config

    cfg = load_config(args.config)
    print(f"config source: {cfg._source or 'built-in defaults'}")
    for key, value in cfg.to_dict().items():
        print(f"  {key}: {value}")
    return 0


def cmd_classify(args) -> int:
    from indexer.rules.engine import RuleEngine

    if args.file:
        with open(args.file, "r") as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        print("error: provide --file or --text", file=sys.stderr)
        return 2

    engine = RuleEngine(config=args.config)
    result = engine.classify_email(text)
    print(json.dumps(result, indent=2))
    return 0


def cmd_ingest_batch(args) -> int:
    from indexer.ingest import batch_ingest

    batch_ingest(args.directory, config=args.config)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tessera-indexer",
        description="Tessera AI Indexer — multi-tier document routing with 100% local inference.",
    )
    parser.add_argument("--version", action="version", version=f"tessera-indexer {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="smoke-test an install (taxonomy, tiers, models)")
    p_check.add_argument("--config", help="path to a config YAML file (or $TESSERA_INDEXER_CONFIG)")

    p_config = sub.add_parser("config", help="print the effective install configuration")
    p_config.add_argument("--config", help="path to a config YAML file (or $TESSERA_INDEXER_CONFIG)")

    p_classify = sub.add_parser("classify", help="classify an email body and print routing JSON")
    p_classify.add_argument("--file", help="path to a text file containing the email body")
    p_classify.add_argument("--text", help="email body text (inline)")
    p_classify.add_argument("--config", help="path to a config YAML file (or $TESSERA_INDEXER_CONFIG)")

    p_ingest = sub.add_parser("ingest-batch", help="process a directory of emails in batch mode")
    p_ingest.add_argument("directory", help="directory containing *_body.txt and *_attachment.pdf files")
    p_ingest.add_argument("--config", help="path to a config YAML file (or $TESSERA_INDEXER_CONFIG)")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = {
        "check": cmd_check,
        "config": cmd_config,
        "classify": cmd_classify,
        "ingest-batch": cmd_ingest_batch,
    }[args.command]
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
