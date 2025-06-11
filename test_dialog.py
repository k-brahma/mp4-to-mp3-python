import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog


def test_directory_selection():
    """ディレクトリ選択の動作をテストする"""
    root = tk.Tk()
    root.withdraw()  # メインウィンドウを隠す
    
    print("ディレクトリ選択ダイアログを開きます...")
    selected_dir = filedialog.askdirectory(title="テスト用ディレクトリを選択")
    
    if selected_dir:
        print(f"選択されたディレクトリ: '{selected_dir}'")
        print(f"タイプ: {type(selected_dir)}")
        print(f"長さ: {len(selected_dir)}")
        print(f"repr: {repr(selected_dir)}")
        
        # パスの詳細分析
        normalized_path = os.path.normpath(selected_dir)
        print(f"正規化パス: '{normalized_path}'")
        print(f"絶対パス: '{os.path.abspath(normalized_path)}'")
        print(f"存在確認: {os.path.exists(normalized_path)}")
        
        # Windowsパス形式に変換
        if sys.platform == "win32":
            windows_path = normalized_path.replace('/', '\\')
            print(f"Windowsパス: '{windows_path}'")
        
        # 実際にエクスプローラーで開いてみる
        try:
            if sys.platform == "win32":
                windows_path = normalized_path.replace('/', '\\')
                print(f"\nエクスプローラーで開く: explorer '{windows_path}'")
                result = subprocess.run(['explorer', windows_path], 
                                      capture_output=True, text=True, check=True)
                print("成功!")
            elif sys.platform == "darwin":
                subprocess.run(['open', normalized_path], check=True)
                print("成功!")
            else:
                subprocess.run(['xdg-open', normalized_path], check=True)
                print("成功!")
                
        except subprocess.CalledProcessError as e:
            print(f"エラー（戻り値: {e.returncode}）: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
        except Exception as e:
            print(f"例外エラー: {e}")
    else:
        print("ディレクトリが選択されませんでした。")
    
    root.destroy()

if __name__ == "__main__":
    test_directory_selection() 