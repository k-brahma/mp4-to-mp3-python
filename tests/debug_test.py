import asyncio
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

from mp4_to_mp3_converter import MP4ToMP3Converter


async def debug_test():
    # 一時ディレクトリを作成
    temp_dir = tempfile.mkdtemp()
    input_file = os.path.join(temp_dir, "test.mp4")
    output_file = os.path.join(temp_dir, "test.mp3")
    
    with open(input_file, 'w') as f:
        f.write("dummy content")
    
    # コンバーターを作成
    with patch('tkinter.Tk'), \
         patch.object(MP4ToMP3Converter, '_check_ffmpeg', return_value=True), \
         patch.object(MP4ToMP3Converter, '_create_widgets'), \
         patch.object(MP4ToMP3Converter, '_setup_async_loop'):
        converter = MP4ToMP3Converter()
    
    # モックを設定
    with patch('asyncio.create_subprocess_exec') as mock_subprocess, \
         patch('os.path.exists') as mock_exists, \
         patch('os.remove') as mock_remove:
        
        call_count = 0
        def exists_side_effect(path):
            nonlocal call_count
            call_count += 1
            print(f"os.path.exists called {call_count} times with path: {path}")
            
            if path == output_file:
                result = call_count > 1  # 2回目以降はTrue
                print(f"Returning: {result}")
                return result
            return False
        
        mock_exists.side_effect = exists_side_effect
        
        mock_process = MagicMock()
        mock_process.communicate = MagicMock(return_value=(b'stdout', b'stderr'))
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process
        
        # テスト実行
        result_file, success, error = await converter._convert_file(input_file, output_file)
        
        print(f"Result: file={result_file}, success={success}, error='{error}'")
        print(f"Process returncode: {mock_process.returncode}")
        print(f"os.path.exists called {call_count} times")
    
    # クリーンアップ
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    asyncio.run(debug_test()) if __name__ == "__main__":
    asyncio.run(debug_test()) 