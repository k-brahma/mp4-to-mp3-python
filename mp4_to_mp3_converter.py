import asyncio
import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from queue import Queue
from tkinter import filedialog, messagebox, ttk
from typing import List, Tuple


class MP4ToMP3Converter:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("MP4 to MP3 Converter")
        self.window.geometry("600x450")
        
        # アプリケーションアイコンの設定（オプション）
        try:
            self.window.iconbitmap('icon.ico')
        except:
            pass  # アイコンファイルがない場合は無視
        
        self.selected_files: List[str] = []
        self.output_dir: str = ""
        self.progress_queue = Queue()
        self.is_converting = False
        
        # ffmpegの存在確認
        if not self._check_ffmpeg():
            self._show_ffmpeg_error()
            return
        
        self._create_widgets()
        self._setup_async_loop()
    
    def _check_ffmpeg(self) -> bool:
        """
        ffmpegが利用可能かチェックする
        
        Returns:
            bool: ffmpegが利用可能な場合True
        """
        try:
            # ffmpegコマンドの存在確認
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False
    
    def _show_ffmpeg_error(self):
        """ffmpegが見つからない場合のエラーダイアログを表示"""
        error_msg = (
            "FFmpegが見つかりません。\n\n"
            "このアプリケーションを使用するには、FFmpegが必要です。\n\n"
            "インストール方法：\n"
            "1. https://ffmpeg.org/download.html からFFmpegをダウンロード\n"
            "2. ffmpeg.exeをシステムのPATHに追加するか、\n"
            "   このアプリケーションと同じフォルダに配置してください\n\n"
            "インストール後、アプリケーションを再起動してください。"
        )
        
        messagebox.showerror("FFmpeg が見つかりません", error_msg)
        self.window.destroy()
    
    def _create_widgets(self):
        # メインフレーム
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # ウィンドウのリサイズ設定
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # タイトル
        title_label = ttk.Label(
            main_frame, 
            text="MP4 to MP3 Converter",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # ファイル選択ボタン
        self.select_files_btn = ttk.Button(
            main_frame,
            text="MP4ファイルを選択",
            command=self._select_files,
            width=30
        )
        self.select_files_btn.grid(row=1, column=0, pady=5)
        
        # 出力ディレクトリ選択ボタン
        self.select_output_btn = ttk.Button(
            main_frame,
            text="出力ディレクトリを選択",
            command=self._select_output_dir,
            width=30
        )
        self.select_output_btn.grid(row=2, column=0, pady=5)
        
        # 出力ディレクトリを開くボタン
        self.open_output_btn = ttk.Button(
            main_frame,
            text="出力ディレクトリを開く",
            command=self._open_output_dir,
            state='disabled',
            width=30
        )
        self.open_output_btn.grid(row=3, column=0, pady=5)
        
        # 変換開始ボタン
        self.convert_btn = ttk.Button(
            main_frame,
            text="変換開始",
            command=self._start_conversion,
            width=30
        )
        self.convert_btn.grid(row=4, column=0, pady=10)
        
        # プログレスバー
        self.progress = ttk.Progressbar(
            main_frame,
            length=400,
            mode='determinate'
        )
        self.progress.grid(row=5, column=0, pady=10, sticky="we")
        
        # ステータスラベル
        self.status_label = ttk.Label(
            main_frame,
            text="ファイルを選択してください",
            font=("Arial", 10)
        )
        self.status_label.grid(row=6, column=0, pady=5)
        
        # ファイルリスト
        listbox_frame = ttk.Frame(main_frame)
        listbox_frame.grid(row=7, column=0, sticky="nsew", pady=10)
        listbox_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        
        self.file_listbox = tk.Listbox(
            listbox_frame,
            height=8
        )
        self.file_listbox.grid(row=0, column=0, sticky="nsew")
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        # FFmpeg情報ラベル
        ffmpeg_info = ttk.Label(
            main_frame,
            text="✓ FFmpeg が利用可能です",
            font=("Arial", 8),
            foreground="green"
        )
        ffmpeg_info.grid(row=8, column=0, pady=5)
    
    def _setup_async_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def _select_files(self):
        if self.is_converting:
            messagebox.showwarning("変換中", "変換処理中は新しいファイルを選択できません。")
            return
            
        files = filedialog.askopenfilenames(
            title="MP4ファイルを選択",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        if files:
            self.selected_files = list(files)
            self.file_listbox.delete(0, tk.END)
            for file in self.selected_files:
                self.file_listbox.insert(tk.END, os.path.basename(file))
            self.status_label.config(text=f"{len(files)}個のファイルが選択されました")
    
    def _select_output_dir(self):
        if self.is_converting:
            messagebox.showwarning("変換中", "変換処理中は出力先を変更できません。")
            return
            
        dir_path = filedialog.askdirectory(title="出力ディレクトリを選択")
        if dir_path:
            self.output_dir = dir_path
            self.status_label.config(text=f"出力先: {os.path.basename(dir_path)}")
            self.open_output_btn.config(state='normal')
    
    def _open_output_dir(self):
        """出力ディレクトリをエクスプローラーで開く"""
        if not self.output_dir:
            messagebox.showwarning("出力先未選択", "出力ディレクトリが選択されていません。")
            return

        if not os.path.exists(self.output_dir):
            messagebox.showwarning("出力先エラー", "出力ディレクトリが存在しません。")
            return

        try:
            if sys.platform == "win32":
                os.startfile(self.output_dir)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(['open', self.output_dir])
            else:  # Linux
                subprocess.run(['xdg-open', self.output_dir])
        except Exception as e:
            messagebox.showerror("エラー", f"ディレクトリを開けませんでした: {str(e)}")
    
    async def _convert_file(self, input_file: str, output_file: str) -> Tuple[str, bool, str]:
        """
        ファイル変換を実行する
        
        Returns:
            Tuple[str, bool, str]: (入力ファイル名, 成功フラグ, エラーメッセージ)
        """
        try:
            # 出力ファイルが既に存在する場合は上書き
            if os.path.exists(output_file):
                os.remove(output_file)
            
            process = await asyncio.create_subprocess_exec(
                'ffmpeg',
                '-i', input_file,
                '-vn',  # 映像を無視
                '-acodec', 'libmp3lame',  # MP3エンコーダー
                '-b:a', '192k',  # ビットレート
                '-y',  # 上書きを自動で許可
                output_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and os.path.exists(output_file):
                return input_file, True, ""
            else:
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "不明なエラー"
                return input_file, False, error_msg
                
        except Exception as e:
            return input_file, False, str(e)
    
    async def _convert_all_files(self):
        if not self.selected_files or not self.output_dir:
            self.status_label.config(text="ファイルと出力先を選択してください")
            return
        
        total_files = len(self.selected_files)
        self.progress['maximum'] = total_files
        self.progress['value'] = 0
        
        success_count = 0
        failed_files = []
        
        tasks = []
        for input_file in self.selected_files:
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_file = os.path.join(self.output_dir, f"{base_name}.mp3")
            tasks.append(self._convert_file(input_file, output_file))
        
        for i, (input_file, success, error_msg) in enumerate(await asyncio.gather(*tasks)):
            self.progress['value'] = i + 1
            
            file_name = os.path.basename(input_file)
            if success:
                success_count += 1
                status = f"✓ {file_name}"
            else:
                failed_files.append((file_name, error_msg))
                status = f"✗ {file_name}"
            
            self.progress_queue.put(status)
            
            # プログレスバーの更新
            self.window.update_idletasks()
        
        # 最終結果の表示
        if failed_files:
            error_details = "\n".join([f"• {name}: {error}" for name, error in failed_files[:5]])
            if len(failed_files) > 5:
                error_details += f"\n...他{len(failed_files) - 5}件"
            
            messagebox.showwarning(
                "変換完了（一部失敗）",
                f"変換完了: {success_count}/{total_files} ファイル\n\n"
                f"失敗したファイル:\n{error_details}"
            )
        else:
            messagebox.showinfo("変換完了", f"すべてのファイル（{total_files}個）の変換が完了しました。")
        
        self.status_label.config(text=f"変換完了: {success_count}/{total_files} ファイル")
    
    def _update_status(self):
        while not self.progress_queue.empty():
            status = self.progress_queue.get()
            self.status_label.config(text=status)
        
        if self.is_converting:
            self.window.after(100, self._update_status)
    
    def _start_conversion(self):
        if not self.selected_files:
            messagebox.showwarning("ファイル未選択", "MP4ファイルを選択してください。")
            return
        
        if not self.output_dir:
            messagebox.showwarning("出力先未選択", "出力ディレクトリを選択してください。")
            return
        
        if self.is_converting:
            messagebox.showwarning("変換中", "既に変換処理が実行中です。")
            return
        
        # 確認ダイアログ
        result = messagebox.askyesno(
            "変換確認",
            f"{len(self.selected_files)}個のファイルを変換しますか？\n\n"
            f"出力先: {self.output_dir}"
        )
        
        if not result:
            return
        
        self.is_converting = True
        self.convert_btn.config(state='disabled')
        self.select_files_btn.config(state='disabled')
        self.select_output_btn.config(state='disabled')
        
        self._update_status()
        
        def run_conversion():
            try:
                self.loop.run_until_complete(self._convert_all_files())
            finally:
                self.is_converting = False
                self.convert_btn.config(state='normal')
                self.select_files_btn.config(state='normal')
                self.select_output_btn.config(state='normal')
        
        threading.Thread(target=run_conversion, daemon=True).start()
    
    def run(self):
        # ウィンドウを中央に配置
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        # 終了時の処理
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self.window.mainloop()
    
    def _on_closing(self):
        """アプリケーション終了時の処理"""
        if self.is_converting:
            result = messagebox.askyesno(
                "変換中です",
                "変換処理が実行中です。終了しますか？"
            )
            if not result:
                return
        
        self.window.destroy()

if __name__ == "__main__":
    try:
        app = MP4ToMP3Converter()
        app.run()
    except Exception as e:
        # 予期しないエラーをキャッチ
        try:
            messagebox.showerror("エラー", f"アプリケーションエラーが発生しました:\n{str(e)}")
        except:
            print(f"Error: {e}")
        sys.exit(1) 