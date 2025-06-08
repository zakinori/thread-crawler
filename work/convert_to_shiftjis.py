import os
import json
import codecs

def convert_json_to_shiftjis(file_path):
    """JSONファイルをUTF-8からShift-JISに変換する"""
    try:
        # UTF-8で読み込み
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 文字列をShift-JISに変換可能な形式に変換
        def convert_to_shiftjis_compatible(obj):
            if isinstance(obj, str):
                # 変換できない文字を置換（'?'に置換）
                try:
                    # まずShift-JISでエンコードできるか試す
                    obj.encode('shift_jis')
                    return obj
                except UnicodeEncodeError:
                    # 変換できない文字を'?'に置換
                    return ''.join(c if ord(c) < 0x10000 else '?' for c in obj)
            elif isinstance(obj, list):
                return [convert_to_shiftjis_compatible(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert_to_shiftjis_compatible(v) for k, v in obj.items()}
            return obj
        
        # データを変換
        converted_data = convert_to_shiftjis_compatible(data)
        
        # Shift-JISで書き込み
        with codecs.open(file_path, 'w', encoding='shift_jis', errors='replace') as f:
            json.dump(converted_data, f, ensure_ascii=False, indent=2)
        
        print(f"変換成功: {file_path}")
        return True
    except Exception as e:
        print(f"変換エラー {file_path}: {str(e)}")
        return False

def main():
    # データディレクトリのパス
    data_dir = 'data'
    
    # 各サブディレクトリを処理
    for subdir in os.listdir(data_dir):
        subdir_path = os.path.join(data_dir, subdir)
        if not os.path.isdir(subdir_path):
            continue
        
        print(f'\n処理中: {subdir}')
        
        # thread_list.jsonを処理
        thread_list_path = os.path.join(subdir_path, 'thread_list.json')
        if os.path.exists(thread_list_path):
            convert_json_to_shiftjis(thread_list_path)
        
        # thread_dataディレクトリ内のJSONファイルを処理
        thread_data_dir = os.path.join(subdir_path, 'thread_data')
        if os.path.exists(thread_data_dir):
            for filename in os.listdir(thread_data_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(thread_data_dir, filename)
                    convert_json_to_shiftjis(file_path)

if __name__ == '__main__':
    main() 