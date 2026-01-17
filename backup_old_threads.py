#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
古いスレッドデータをバックアップフォルダへ退避するスクリプト

・dataフォルダのthread_data内のjsonにおいて、dateの最大日付が三カ月前よりも過去のスレッドデータを_backupフォルダへ退避する
・_backupフォルダへ退避する内容はdataフォルダの構造を踏襲する
・_backupフォルダへ退避するのはthread_data内のjsonファイルと、thread_list.jsonの該当リスト部分とする
・update.logは退避対象外とする
"""

import json
import os
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple


def parse_date(date_str: str) -> Optional[datetime]:
    """
    日付文字列をパースする
    形式: "2010/10/24(日) 17:41:27" または "2025/06/19(木) 06:41:43.87"
    """
    try:
        # 日付部分を抽出 (例: "2010/10/24(日) 17:41:27" -> "2010/10/24 17:41:27")
        # 括弧と曜日を除去
        date_part = re.sub(r'\([^)]+\)', '', date_str).strip()
        # ミリ秒部分があれば除去
        date_part = re.sub(r'\.\d+$', '', date_part)
        
        # パースを試みる
        for fmt in ['%Y/%m/%d %H:%M:%S', '%Y/%m/%d %H:%M']:
            try:
                return datetime.strptime(date_part, fmt)
            except ValueError:
                continue
        
        return None
    except Exception:
        return None


def get_max_date_from_thread(thread_file: Path) -> Optional[datetime]:
    """
    スレッドJSONファイルから最大日付を取得する
    """
    try:
        with open(thread_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        max_date = None
        if 'responses' in data and isinstance(data['responses'], list):
            for response in data['responses']:
                if 'date' in response:
                    date_obj = parse_date(response['date'])
                    if date_obj:
                        if max_date is None or date_obj > max_date:
                            max_date = date_obj
        
        return max_date
    except Exception as e:
        print(f"警告: {thread_file} の読み込みに失敗しました: {e}")
        return None


def extract_thread_id_from_url(url: str) -> Optional[str]:
    """
    URLからスレッドIDを抽出する
    例: "https://ikura.2ch.sc/test/read.cgi/oversea/1287909687" -> "1287909687"
    """
    match = re.search(r'/(\d+)$', url)
    if match:
        return match.group(1)
    return None


def get_thread_filename_from_url(url: str) -> str:
    """
    URLからスレッドJSONファイル名を生成する
    例: "https://ikura.2ch.sc/test/read.cgi/oversea/1287909687" -> "thread_1287909687.json"
    """
    thread_id = extract_thread_id_from_url(url)
    if thread_id:
        return f"thread_{thread_id}.json"
    return ""


def backup_threads(data_dir: Path = Path('data'), months: int = 3):
    """
    古いスレッドデータをバックアップフォルダへ退避する
    
    Args:
        data_dir: データディレクトリのパス
        months: 何カ月前より古いデータを退避するか
    """
    # 基準日（3カ月前）
    cutoff_date = datetime.now() - timedelta(days=months * 30)
    print(f"基準日: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"この日付より古いスレッドをバックアップします\n")
    
    # バックアップディレクトリ（プロジェクトルートに配置）
    backup_dir = data_dir.parent / '_backup'
    backup_dir.mkdir(exist_ok=True)
    
    # dataディレクトリ内の各サブディレクトリを処理
    for subdir in data_dir.iterdir():
        if not subdir.is_dir() or subdir.name == '_backup':
            continue
        
        print(f"処理中: {subdir.name}")
        
        thread_data_dir = subdir / 'thread_data'
        thread_list_file = subdir / 'thread_list.json'
        
        if not thread_data_dir.exists():
            print(f"  スキップ: thread_dataディレクトリが存在しません")
            continue
        
        # バックアップ先のディレクトリを作成
        backup_subdir = backup_dir / subdir.name
        backup_thread_data_dir = backup_subdir / 'thread_data'
        backup_thread_data_dir.mkdir(parents=True, exist_ok=True)
        
        # thread_list.jsonを読み込む
        threads_to_backup = []
        threads_to_keep = []
        
        if thread_list_file.exists():
            with open(thread_list_file, 'r', encoding='utf-8') as f:
                thread_list_data = json.load(f)
        else:
            thread_list_data = {'threads': []}
        
        # thread_data内の各JSONファイルをチェック
        thread_files_to_backup = []
        for thread_file in thread_data_dir.glob('thread_*.json'):
            max_date = get_max_date_from_thread(thread_file)
            
            if max_date is None:
                print(f"  警告: {thread_file.name} の日付を取得できませんでした。スキップします。")
                continue
            
            if max_date < cutoff_date:
                # バックアップ対象
                thread_files_to_backup.append(thread_file)
                
                # thread_list.jsonから該当するエントリを探す
                # ファイル名からthread_idを抽出 (例: "thread_1287909687.json" -> "1287909687")
                thread_id = thread_file.stem.replace('thread_', '')
                for thread in thread_list_data.get('threads', []):
                    if 'url' in thread:
                        file_thread_id = extract_thread_id_from_url(thread['url'])
                        if file_thread_id == thread_id:
                            threads_to_backup.append(thread)
                            break
        
        # バックアップ対象のファイルを移動
        if thread_files_to_backup:
            print(f"  バックアップ対象: {len(thread_files_to_backup)} ファイル")
            
            for thread_file in thread_files_to_backup:
                backup_file = backup_thread_data_dir / thread_file.name
                shutil.move(str(thread_file), str(backup_file))
                print(f"    移動: {thread_file.name}")
            
            # thread_list.jsonを更新
            if thread_list_file.exists():
                # 保持するスレッドを抽出
                threads_to_keep = [
                    t for t in thread_list_data.get('threads', [])
                    if t not in threads_to_backup
                ]
                
                # 元のthread_list.jsonを更新
                thread_list_data['threads'] = threads_to_keep
                with open(thread_list_file, 'w', encoding='utf-8') as f:
                    json.dump(thread_list_data, f, ensure_ascii=False, indent=2)
            
            # バックアップ側のthread_list.jsonを更新
            backup_thread_list_file = backup_subdir / 'thread_list.json'
            if backup_thread_list_file.exists():
                with open(backup_thread_list_file, 'r', encoding='utf-8') as f:
                    backup_thread_list_data = json.load(f)
            else:
                backup_thread_list_data = {'threads': []}
            
            # 既存のURLをセットに変換して重複チェック用に使用
            existing_urls = {t.get('url') for t in backup_thread_list_data.get('threads', []) if 'url' in t}
            
            # バックアップ側のthread_list.jsonに追加（重複を避ける）
            for thread in threads_to_backup:
                if 'url' in thread and thread['url'] not in existing_urls:
                    backup_thread_list_data['threads'].append(thread)
                    existing_urls.add(thread['url'])
            
            with open(backup_thread_list_file, 'w', encoding='utf-8') as f:
                json.dump(backup_thread_list_data, f, ensure_ascii=False, indent=2)
            
            print(f"  thread_list.jsonを更新しました（保持: {len(threads_to_keep)}, バックアップ: {len(threads_to_backup)}）")
        else:
            print(f"  バックアップ対象なし")
        
        print()
    
    print("バックアップ処理が完了しました")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='古いスレッドデータをバックアップフォルダへ退避する')
    parser.add_argument('--data-dir', type=str, default='data', help='データディレクトリのパス（デフォルト: data）')
    parser.add_argument('--months', type=int, default=3, help='何カ月前より古いデータを退避するか（デフォルト: 3）')
    
    args = parser.parse_args()
    
    backup_threads(data_dir=Path(args.data_dir), months=args.months)
