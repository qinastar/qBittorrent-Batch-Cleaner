import os
import sys
import shutil
from PyInstaller.__main__ import run

def clean_build():
    """清理构建文件"""
    dirs_to_clean = ['build', 'dist']
    files_to_clean = ['*.spec']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已删除目录: {dir_name}")
    
    for pattern in files_to_clean:
        for file in os.listdir('.'):
            if file.endswith('.spec'):
                os.remove(file)
                print(f"已删除文件: {file}")

def build():
    """打包应用程序"""
    # 清理旧的构建文件
    clean_build()
    
    # PyInstaller 参数
    opts = [
        'app.py',                     # 主程序文件
        '--name=qBittorrent-Cleaner', # 输出文件名
        '--noconsole',                # 不显示控制台窗口
        '--onefile',                  # 打包成单个文件
        '--windowed',                 # Windows下不显示控制台
        '--clean',                    # 清理临时文件
        # 排除不需要的模块
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=PIL',
        '--exclude-module=pandas',
        '--exclude-module=scipy',
        '--exclude-module=tkinter',
        '--exclude-module=PyQt6.QtQml',
        '--exclude-module=PyQt6.QtQuick',
        '--exclude-module=PyQt6.QtSql',
        '--exclude-module=PyQt6.QtTest',
        '--exclude-module=PyQt6.QtWebEngine',
        '--exclude-module=PyQt6.QtWebEngineCore',
        '--exclude-module=PyQt6.QtWebEngineWidgets',
        # 添加必要的数据文件
        '--add-data=config.json;.' if os.path.exists('config.json') else None,
        # 添加隐藏导入
        '--hidden-import=PyQt6.sip',
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtWidgets',
    ]
    
    # 移除None值
    opts = [opt for opt in opts if opt is not None]
    
    print("开始打包...")
    run(opts)
    print("打包完成！")
    
    # 检查是否成功创建了可执行文件
    exe_name = 'qBittorrent-Cleaner.exe' if sys.platform == 'win32' else 'qBittorrent-Cleaner'
    exe_path = os.path.join('dist', exe_name)
    
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"\n构建成功！")
        print(f"可执行文件位置: {exe_path}")
        print(f"文件大小: {size_mb:.2f} MB")
    else:
        print("\n构建似乎失败了，没有找到输出文件")

if __name__ == "__main__":
    build() 