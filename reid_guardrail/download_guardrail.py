"""Download pinned official model files locally; never execute remote model code."""
import argparse
from pathlib import Path

from .data import write_json


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--revision", default="b19585c4ae526f9539f7e3213f56624222c0526e")
    p.add_argument("--out", default="models/modernbert-tr-guardrail")
    args = p.parse_args()
    from huggingface_hub import snapshot_download
    snapshot_download(repo_id="ytu-ce-cosmos/modernbert-tr-guardrail", revision=args.revision,
                      local_dir=args.out, cache_dir=str(Path.cwd() / ".cache/huggingface/hub"),
                      allow_patterns=["config.json", "model.safetensors", "tokenizer.json", "tokenizer_config.json"])
    write_json(Path(args.out) / "revision.json", {"repository": "ytu-ce-cosmos/modernbert-tr-guardrail", "revision": args.revision})
    print(f"Model hazır: {args.out}")


if __name__ == "__main__":
    main()
