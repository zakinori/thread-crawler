import os

def remove_zone_identifiers(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(':Zone.Identifier'):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"削除成功: {file_path}")
                except Exception as e:
                    print(f"削除エラー {file_path}: {str(e)}")

if __name__ == '__main__':
    data_dir = 'data'
    print("Zone.Identifierファイルの削除を開始します...")
    remove_zone_identifiers(data_dir)
    print("処理が完了しました。") 