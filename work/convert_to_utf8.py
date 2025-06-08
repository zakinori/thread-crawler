import os
import json
import chardet

def convert_to_utf8(file_path):
    try:
        # ファイルの内容を読み込む
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        
        # エンコーディングを検出
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        
        if encoding is None:
            # エンコーディングが検出できない場合は、UTF-8として読み込みを試みる
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except UnicodeDecodeError:
                # UTF-8で読み込めない場合は、Shift-JISとして試みる
                with open(file_path, 'r', encoding='shift_jis') as f:
                    data = json.load(f)
        else:
            # 検出されたエンコーディングで読み込む
            with open(file_path, 'r', encoding=encoding) as f:
                data = json.load(f)
        
        # UTF-8で書き込み
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"変換成功: {file_path}")
        return True
    except Exception as e:
        print(f"変換エラー {file_path}: {str(e)}")
        return False

def main():
    data_dir = 'data'
    
    # 各サブディレクトリを処理
    for subdir in os.listdir(data_dir):
        subdir_path = os.path.join(data_dir, subdir)
        if not os.path.isdir(subdir_path):
            continue
            
        print(f"\n処理中: {subdir}")
        
        # thread_list.jsonを処理
        thread_list_path = os.path.join(subdir_path, 'thread_list.json')
        if os.path.exists(thread_list_path):
            convert_to_utf8(thread_list_path)
        
        # thread_dataディレクトリ内のJSONファイルを処理
        thread_data_dir = os.path.join(subdir_path, 'thread_data')
        if os.path.exists(thread_data_dir):
            for filename in os.listdir(thread_data_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(thread_data_dir, filename)
                    convert_to_utf8(file_path)

if __name__ == '__main__':
    main() 