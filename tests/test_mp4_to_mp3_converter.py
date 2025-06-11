import asyncio
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from mp4_to_mp3_converter import MP4ToMP3Converter


class TestMP4ToMP3ConverterCheckFfmpeg:
    """ffmpegチェック機能のテストクラス"""

    def test_check_ffmpeg_success(self):
        """ffmpegが利用可能な場合のテスト"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            with patch('tkinter.Tk'), \
                 patch.object(MP4ToMP3Converter, '_create_widgets'), \
                 patch.object(MP4ToMP3Converter, '_setup_async_loop'):
                converter = MP4ToMP3Converter()
                result = converter._check_ffmpeg()
                assert result is True

    def test_check_ffmpeg_failure(self):
        """ffmpegが利用不可能な場合のテスト"""
        with patch('subprocess.run', side_effect=FileNotFoundError):
            with patch('tkinter.Tk'), \
                 patch.object(MP4ToMP3Converter, '_create_widgets'), \
                 patch.object(MP4ToMP3Converter, '_setup_async_loop'):
                converter = MP4ToMP3Converter()
                result = converter._check_ffmpeg()
                assert result is False


class TestMP4ToMP3ConverterConvertFile:
    """ファイル変換機能のテストクラス"""

    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリを作成するフィクスチャ"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def converter(self):
        """MP4ToMP3Converterのインスタンスを作成するフィクスチャ"""
        with patch('tkinter.Tk'), \
             patch.object(MP4ToMP3Converter, '_check_ffmpeg', return_value=True), \
             patch.object(MP4ToMP3Converter, '_create_widgets'), \
             patch.object(MP4ToMP3Converter, '_setup_async_loop'):
            converter = MP4ToMP3Converter()
            return converter

    @pytest.mark.asyncio
    async def test_convert_file_success(self, converter, temp_dir):
        """ファイル変換の成功テスト"""
        input_file = os.path.join(temp_dir, "test.mp4")
        output_file = os.path.join(temp_dir, "test.mp3")
        
        with open(input_file, 'w') as f:
            f.write("dummy content")
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess, \
             patch('os.remove') as mock_remove:
            
            mock_process = MagicMock()
            # communicateメソッドを非同期コルーチンとしてモック
            async def mock_communicate():
                return (b'stdout', b'stderr')
            mock_process.communicate = mock_communicate
            mock_process.returncode = 0  # 成功を示すリターンコード
            mock_subprocess.return_value = mock_process
            
            # _convert_file内でos.path.existsが呼ばれるタイミングで出力ファイルが存在すると仮定
            with patch('mp4_to_mp3_converter.os.path.exists') as mock_exists:
                # 最初の呼び出し（既存ファイルチェック）ではFalse、
                # 2回目の呼び出し（変換後チェック）ではTrueを返す
                mock_exists.side_effect = [False, True]
                
                result_file, success, error = await converter._convert_file(input_file, output_file)
                
                assert success is True, f"Expected success=True, got success={success}, error='{error}'"
                assert result_file == input_file
                assert error == ""
                mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_file_failure(self, converter, temp_dir):
        """ファイル変換の失敗テスト"""
        input_file = os.path.join(temp_dir, "test.mp4")
        output_file = os.path.join(temp_dir, "test.mp3")
        
        with patch('asyncio.create_subprocess_exec', side_effect=Exception("Test error")):
            result_file, success, error = await converter._convert_file(input_file, output_file)
            
            assert success is False
            assert result_file == input_file
            assert error == "Test error"


class TestMP4ToMP3ConverterOpenOutputDir:
    """出力ディレクトリを開く機能のテストクラス"""

    @pytest.fixture
    def converter(self):
        """MP4ToMP3Converterのインスタンスを作成するフィクスチャ"""
        with patch('tkinter.Tk'), \
             patch.object(MP4ToMP3Converter, '_check_ffmpeg', return_value=True), \
             patch.object(MP4ToMP3Converter, '_create_widgets'), \
             patch.object(MP4ToMP3Converter, '_setup_async_loop'):
            converter = MP4ToMP3Converter()
            return converter

    def test_open_output_dir_windows(self, converter):
        """Windows環境で出力ディレクトリを開くテスト"""
        test_dir = "/test/output/dir"
        converter.output_dir = test_dir
        
        with patch('os.path.exists', return_value=True), \
             patch('os.startfile') as mock_startfile, \
             patch('sys.platform', 'win32'), \
             patch('tkinter.messagebox.showwarning'), \
             patch('tkinter.messagebox.showerror'):
            converter._open_output_dir()
            mock_startfile.assert_called_once_with(test_dir)

    def test_open_output_dir_not_exists(self, converter):
        """存在しない出力ディレクトリを開くテスト"""
        test_dir = "/test/output/dir"
        converter.output_dir = test_dir
        
        with patch('os.path.exists', return_value=False), \
             patch('os.startfile') as mock_startfile, \
             patch('tkinter.messagebox.showwarning') as mock_warning:
            converter._open_output_dir()
            mock_startfile.assert_not_called()
            mock_warning.assert_called_once() 