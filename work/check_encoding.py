import os
import json
import chardet

def check_file_encoding(file_path):
    try:
        # ファイルの内容を読み込む
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        
        # エンコーディングを検出
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        confidence = result['confidence']
        
        # JSONとして読み込めるか確認
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                json.load(f)
            json_valid = True
        except json.JSONDecodeError:
            json_valid = False
        except UnicodeDecodeError:
            json_valid = False
        
        return {
            'encoding': encoding,
            'confidence': confidence,
            'json_valid': json_valid
        }
    except Exception as e:
        return {
            'error': str(e)
        }

def main():
    data_dir = 'data'
    
    # 各サブディレクトリを処理
    for subdir in os.listdir(data_dir):
        subdir_path = os.path.join(data_dir, subdir)
        if not os.path.isdir(subdir_path):
            continue
            
        print(f"\n処理中: {subdir}")
        
        # thread_list.jsonをチェック
        thread_list_path = os.path.join(subdir_path, 'thread_list.json')
        if os.path.exists(thread_list_path):
            result = check_file_encoding(thread_list_path)
            print(f"thread_list.json: {result}")
        
        # thread_dataディレクトリ内のJSONファイルをチェック
        thread_data_dir = os.path.join(subdir_path, 'thread_data')
        if os.path.exists(thread_data_dir):
            for filename in os.listdir(thread_data_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(thread_data_dir, filename)
                    result = check_file_encoding(file_path)
                    print(f"{filename}: {result}")

if __name__ == '__main__':
    main() 