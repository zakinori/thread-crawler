#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_backup フォルダから data フォルダへスレッドデータを復元するスクリプト

・thread_data: data に無ければ move、あればレス最大日付（同値ならレス数）で新旧を比較
  - _backup の方が新しい/多い → data を上書きし _backup から削除
  - data の方が新しい/多い、または同等 → data を維持し _backup から削除
・thread_list.json: data に同一 URL の行が無い場合のみ _backup から追加
"""

import argparse
import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from backup_old_threads import get_max_date_from_thread


@dataclass
class ThreadFileStats:
    max_date: Optional[datetime]
    response_count: int


@dataclass
class BoardRestorePlan:
    board_name: str
    move_files: List[str] = field(default_factory=list)
    overwrite_files: List[str] = field(default_factory=list)
    keep_data_files: List[str] = field(default_factory=list)
    thread_list_inserts: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def get_thread_file_stats(thread_file: Path) -> ThreadFileStats:
    max_date = get_max_date_from_thread(thread_file)
    try:
        with open(thread_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        response_count = len(data.get('responses', []))
    except Exception:
        response_count = 0
    return ThreadFileStats(max_date=max_date, response_count=response_count)


def backup_is_preferred(backup_stats: ThreadFileStats, data_stats: ThreadFileStats) -> bool:
    """_backup 側を data へ反映すべきか（data が減らないよう、より新しい/多い方を採用）"""
    if backup_stats.max_date is None and data_stats.max_date is None:
        return backup_stats.response_count > data_stats.response_count
    if backup_stats.max_date is None:
        return False
    if data_stats.max_date is None:
        return True
    if backup_stats.max_date > data_stats.max_date:
        return True
    if backup_stats.max_date < data_stats.max_date:
        return False
    return backup_stats.response_count > data_stats.response_count


def format_stats(stats: ThreadFileStats) -> str:
    date_str = stats.max_date.strftime('%Y-%m-%d %H:%M:%S') if stats.max_date else 'N/A'
    return f"max_date={date_str}, responses={stats.response_count}"


def load_thread_list(path: Path) -> dict:
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'threads': []}


def save_thread_list(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def plan_board_restore(
    board_name: str,
    backup_subdir: Path,
    data_subdir: Path,
) -> BoardRestorePlan:
    plan = BoardRestorePlan(board_name=board_name)
    backup_thread_data_dir = backup_subdir / 'thread_data'
    data_thread_data_dir = data_subdir / 'thread_data'

    if not backup_thread_data_dir.exists():
        return plan

    data_thread_data_dir.mkdir(parents=True, exist_ok=True)

    for backup_file in sorted(backup_thread_data_dir.glob('thread_*.json')):
        data_file = data_thread_data_dir / backup_file.name

        if not data_file.exists():
            plan.move_files.append(backup_file.name)
            continue

        try:
            backup_stats = get_thread_file_stats(backup_file)
            data_stats = get_thread_file_stats(data_file)
        except Exception as exc:
            plan.errors.append(f"{backup_file.name}: {exc}")
            continue

        if backup_is_preferred(backup_stats, data_stats):
            plan.overwrite_files.append(
                f"{backup_file.name} (backup: {format_stats(backup_stats)} / data: {format_stats(data_stats)})"
            )
        else:
            plan.keep_data_files.append(backup_file.name)

    backup_thread_list = load_thread_list(backup_subdir / 'thread_list.json')
    data_thread_list = load_thread_list(data_subdir / 'thread_list.json')
    existing_urls = {
        thread['url']
        for thread in data_thread_list.get('threads', [])
        if 'url' in thread
    }

    for thread in backup_thread_list.get('threads', []):
        url = thread.get('url')
        if url and url not in existing_urls:
            title = thread.get('title', '')
            plan.thread_list_inserts.append(f"{url} ({title})")

    return plan


def apply_board_restore(
    board_name: str,
    backup_subdir: Path,
    data_subdir: Path,
    plan: BoardRestorePlan,
) -> None:
    backup_thread_data_dir = backup_subdir / 'thread_data'
    data_thread_data_dir = data_subdir / 'thread_data'
    data_thread_data_dir.mkdir(parents=True, exist_ok=True)

    for filename in plan.move_files:
        backup_file = backup_thread_data_dir / filename
        data_file = data_thread_data_dir / filename
        shutil.move(str(backup_file), str(data_file))

    for entry in plan.overwrite_files:
        filename = entry.split(' ', 1)[0]
        backup_file = backup_thread_data_dir / filename
        data_file = data_thread_data_dir / filename
        shutil.move(str(backup_file), str(data_file))

    for filename in plan.keep_data_files:
        backup_file = backup_thread_data_dir / filename
        if backup_file.exists():
            backup_file.unlink()

    backup_thread_list = load_thread_list(backup_subdir / 'thread_list.json')
    data_thread_list = load_thread_list(data_subdir / 'thread_list.json')
    existing_urls = {
        thread['url']
        for thread in data_thread_list.get('threads', [])
        if 'url' in thread
    }

    for thread in backup_thread_list.get('threads', []):
        url = thread.get('url')
        if url and url not in existing_urls:
            data_thread_list.setdefault('threads', []).append(thread)
            existing_urls.add(url)

    if plan.thread_list_inserts:
        save_thread_list(data_subdir / 'thread_list.json', data_thread_list)

    backup_thread_list_path = backup_subdir / 'thread_list.json'
    remaining_files = list(backup_thread_data_dir.glob('thread_*.json'))
    if not remaining_files and backup_thread_list_path.exists():
        backup_thread_list_path.unlink()


def print_plan(plans: List[BoardRestorePlan]) -> None:
    totals = {
        'move': 0,
        'overwrite': 0,
        'keep_data': 0,
        'thread_list': 0,
        'errors': 0,
    }

    print('=== dry-run: 復元計画 ===\n')

    for plan in plans:
        move_count = len(plan.move_files)
        overwrite_count = len(plan.overwrite_files)
        keep_count = len(plan.keep_data_files)
        insert_count = len(plan.thread_list_inserts)
        error_count = len(plan.errors)

        totals['move'] += move_count
        totals['overwrite'] += overwrite_count
        totals['keep_data'] += keep_count
        totals['thread_list'] += insert_count
        totals['errors'] += error_count

        print(f"[{plan.board_name}]")
        print(f"  move (data に無い): {move_count}")
        print(f"  overwrite (_backup 優先): {overwrite_count}")
        print(f"  keep data (_backup のみ削除): {keep_count}")
        print(f"  thread_list 追加: {insert_count}")
        if plan.errors:
            print(f"  エラー: {error_count}")

        if plan.overwrite_files:
            print('  上書き候補:')
            for entry in plan.overwrite_files:
                print(f"    - {entry}")

        if plan.errors:
            print('  エラー詳細:')
            for entry in plan.errors:
                print(f"    - {entry}")

        print()

    print('=== 合計 ===')
    print(f"move: {totals['move']}")
    print(f"overwrite: {totals['overwrite']}")
    print(f"keep data: {totals['keep_data']}")
    print(f"thread_list 追加: {totals['thread_list']}")
    print(f"errors: {totals['errors']}")
    print()


def restore_threads(
    data_dir: Path = Path('data'),
    backup_dir: Path = Path('_backup'),
    execute: bool = False,
) -> None:
    if not backup_dir.exists():
        print(f"エラー: バックアップディレクトリが存在しません: {backup_dir}")
        return

    plans: List[BoardRestorePlan] = []

    for backup_subdir in sorted(backup_dir.iterdir()):
        if not backup_subdir.is_dir():
            continue

        board_name = backup_subdir.name
        data_subdir = data_dir / board_name
        plan = plan_board_restore(board_name, backup_subdir, data_subdir)
        plans.append(plan)

    print_plan(plans)

    if not execute:
        print('本実行する場合: python3 restore_old_threads.py --execute')
        return

    print('=== 本実行開始 ===\n')

    for plan in plans:
        backup_subdir = backup_dir / plan.board_name
        data_subdir = data_dir / plan.board_name
        print(f"処理中: {plan.board_name}")
        apply_board_restore(plan.board_name, backup_subdir, data_subdir, plan)
        print(f"  完了: move={len(plan.move_files)}, overwrite={len(plan.overwrite_files)}, "
              f"keep data={len(plan.keep_data_files)}, thread_list 追加={len(plan.thread_list_inserts)}")

    print('\n復元処理が完了しました')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='_backup から data へスレッドデータを復元する')
    parser.add_argument('--data-dir', type=str, default='data', help='データディレクトリのパス（デフォルト: data）')
    parser.add_argument('--backup-dir', type=str, default='_backup', help='バックアップディレクトリのパス（デフォルト: _backup）')
    parser.add_argument('--execute', action='store_true', help='dry-run ではなく本実行する')

    args = parser.parse_args()

    restore_threads(
        data_dir=Path(args.data_dir),
        backup_dir=Path(args.backup_dir),
        execute=args.execute,
    )
