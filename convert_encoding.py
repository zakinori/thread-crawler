#!/usr/bin/env python3
"""UTF-8 の JSON 等を Shift_JIS (cp932) へ変換する。

未対応文字は '?' に置換し、エラーでは止めない（cron 向け）。
出力は --dst 配下に --base からの相対パスを保って作成する。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_SRC = Path("data")
DEFAULT_DST = Path("convert_data")
DEFAULT_ENCODING_IN = "utf-8"
DEFAULT_ENCODING_OUT = "cp932"  # Windows 互換の Shift_JIS
REPLACE_ERRORS = "replace"


def resolve_base(src: Path, base: Path | None) -> Path:
    """相対パス計算用のソースルートを決める。"""
    if base is not None:
        return base.resolve()
    if src.is_dir():
        return src.resolve()
    # 単一ファイル: 既定の data/ 配下なら data をルートにする
    resolved = src.resolve()
    data_root = DEFAULT_SRC.resolve()
    try:
        resolved.relative_to(data_root)
        return data_root
    except ValueError:
        return resolved.parent


def collect_files(src: Path) -> list[Path]:
    if src.is_file():
        return [src]
    if not src.is_dir():
        raise FileNotFoundError(f"変換対象が存在しません: {src}")
    return sorted(p for p in src.rglob("*") if p.is_file())


def convert_file(src_file: Path, dst_file: Path) -> None:
    text = src_file.read_text(encoding=DEFAULT_ENCODING_IN)
    dst_file.parent.mkdir(parents=True, exist_ok=True)
    dst_file.write_text(text, encoding=DEFAULT_ENCODING_OUT, errors=REPLACE_ERRORS)


def run(src: Path, dst: Path, base: Path | None) -> int:
    src = src.resolve()
    dst = dst.resolve()
    base_root = resolve_base(src, base)

    files = collect_files(src)
    if not files:
        print(f"変換対象ファイルがありません: {src}")
        return 0

    converted = 0
    for src_file in files:
        try:
            rel = src_file.resolve().relative_to(base_root)
        except ValueError:
            print(
                f"警告: --base ({base_root}) 配下ではないためスキップ: {src_file}",
                file=sys.stderr,
            )
            continue
        dst_file = dst / rel
        convert_file(src_file, dst_file)
        converted += 1
        print(f"変換: {src_file} -> {dst_file}")

    print(f"完了: {converted} ファイルを {dst} へ出力しました")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="UTF-8 ファイルを Shift_JIS (cp932) に変換し、ディレクトリ構成を保って出力する"
    )
    parser.add_argument(
        "--src",
        type=Path,
        default=DEFAULT_SRC,
        help=f"変換対象のファイルまたはディレクトリ (default: {DEFAULT_SRC})",
    )
    parser.add_argument(
        "--dst",
        type=Path,
        default=DEFAULT_DST,
        help=f"出力先ルートディレクトリ (default: {DEFAULT_DST})",
    )
    parser.add_argument(
        "--base",
        type=Path,
        default=None,
        help="相対パス計算の基準ディレクトリ (未指定時: ディレクトリ指定なら --src、ファイル指定なら data)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return run(args.src, args.dst, args.base)
    except FileNotFoundError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
