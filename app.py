import sys
import json
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QWidget, 
                            QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, 
                            QDialog, QLineEdit, QFormLayout, QMessageBox,
                            QTabWidget, QScrollArea, QStyleFactory, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon
from check_local_torrents import check_local_torrents
from delete_remote_torrents import delete_remote_torrents
from check_deleted_torrents import check_deleted_torrents, delete_site_deleted_torrents

DEFAULT_CONFIG = {
    "local_server": {
        "url": "http://localhost:8080",
        "username": "admin",
        "password": "adminadmin",
        "tag": "test",
        "category": ""
    },
    "remote_servers": [
        {
            "name": "远程服务器1",
            "url": "http://example.com:8080",
            "username": "admin",
            "password": "adminadmin"
        }
    ]
}

def ensure_config_exists():
    """确保配置文件存在，如果不存在则创建默认配置"""
    if not os.path.exists("config.json"):
        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=4)
            print("已创建默认配置文件 config.json")
        except Exception as e:
            print(f"创建默认配置文件时发生错误: {str(e)}")

def set_dark_theme(app):
    """设置深色主题"""
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # 设置深色调色板
    dark_palette = QPalette()
    
    # 设置颜色
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    
    # 设置禁用状态的颜色
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(127, 127, 127))
    
    app.setPalette(dark_palette)
    
    # 设置深色样式表
    app.setStyleSheet("""
        QToolTip { 
            color: #ffffff; 
            background-color: #2a82da;
            border: 1px solid white;
            padding: 5px;
            border-radius: 3px;
        }
        QPushButton {
            background-color: #424242;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            min-width: 100px;
        }
        QPushButton:hover {
            background-color: #4f4f4f;
        }
        QPushButton:pressed {
            background-color: #383838;
        }
        QTabWidget::pane {
            border: 1px solid #424242;
            border-radius: 4px;
        }
        QTabBar::tab {
            background-color: #353535;
            color: #ffffff;
            padding: 8px 16px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background-color: #424242;
        }
        QLineEdit, QTextEdit {
            background-color: #2b2b2b;
            border: 1px solid #424242;
            border-radius: 4px;
            padding: 5px;
            color: #ffffff;
        }
        QLineEdit:focus, QTextEdit:focus {
            border: 1px solid #2a82da;
        }
    """)

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(600)
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 创建选项卡
        tab_widget = QTabWidget()
        
        # 本地服务器设置
        local_widget = QWidget()
        local_layout = QFormLayout()
        
        self.local_url = QLineEdit()
        self.local_username = QLineEdit()
        self.local_password = QLineEdit()
        self.local_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.local_tag = QLineEdit()
        self.local_category = QLineEdit()
        
        local_layout.addRow("服务器地址:", self.local_url)
        local_layout.addRow("用户名:", self.local_username)
        local_layout.addRow("密码:", self.local_password)
        local_layout.addRow("标签:", self.local_tag)
        local_layout.addRow("分类(可选):", self.local_category)
        
        local_widget.setLayout(local_layout)
        tab_widget.addTab(local_widget, "本地服务器")
        
        # 远程服务器设置
        remote_widget = QWidget()
        remote_layout = QFormLayout()
        
        self.remote_servers_text = QTextEdit()
        self.remote_servers_text.setPlaceholderText("""示例格式:
[
    {
        "name": "服务器1",
        "url": "http://server1:8080",
        "username": "admin",
        "password": "adminadmin"
    }
]""")
        
        remote_layout.addRow("远程服务器配置 (JSON格式):", self.remote_servers_text)
        remote_widget.setLayout(remote_layout)
        tab_widget.addTab(remote_widget, "远程服务器")
        
        layout.addWidget(tab_widget)
        
        # 按钮
        buttons = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_config)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)
        
        self.setLayout(layout)

    def load_config(self):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
                
                # 加载本地服务器配置
                local_server = config.get("local_server", {})
                self.local_url.setText(local_server.get("url", ""))
                self.local_username.setText(local_server.get("username", ""))
                self.local_password.setText(local_server.get("password", ""))
                self.local_tag.setText(local_server.get("tag", ""))
                self.local_category.setText(local_server.get("category", ""))
                
                # 加载远程服务器配置
                remote_servers = config.get("remote_servers", [])
                self.remote_servers_text.setText(
                    json.dumps(remote_servers, ensure_ascii=False, indent=4)
                )
        except FileNotFoundError:
            pass

    def save_config(self):
        try:
            config = {
                "local_server": {
                    "url": self.local_url.text(),
                    "username": self.local_username.text(),
                    "password": self.local_password.text(),
                    "tag": self.local_tag.text(),
                    "category": self.local_category.text()
                },
                "remote_servers": json.loads(self.remote_servers_text.toPlainText())
            }
            
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            
            QMessageBox.information(self, "成功", "配置已保存")
            self.accept()
        except json.JSONDecodeError:
            QMessageBox.critical(self, "错误", "远程服务器配置的JSON格式无效")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置时发生错误: {str(e)}")

class WorkerThread(QThread):
    output = pyqtSignal(str)
    
    def __init__(self, function, debug_mode=None):
        super().__init__()
        self.function = function
        self.debug_mode = debug_mode
        
    def run(self):
        # 重定向标准输出到自定义输出
        class StreamWrapper:
            def __init__(self, output_signal):
                self.output_signal = output_signal
                
            def write(self, text):
                if text.strip():
                    self.output_signal.emit(text.strip())
                    
            def flush(self):
                pass
        
        # 保存原始的标准输出
        old_stdout = sys.stdout
        sys.stdout = StreamWrapper(self.output)
        
        try:
            if self.debug_mode is not None:
                self.function(debug_mode=self.debug_mode)
            else:
                self.function()
        except Exception as e:
            self.output.emit(f"发生错误: {str(e)}")
        finally:
            # 恢复原始的标准输出
            sys.stdout = old_stdout

    def check_deleted(self):
        """检查被站点删除的种子"""
        self.log_output.clear()
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            
            def worker_function():
                return check_deleted_torrents(config["local_server"])
            
            self.worker = WorkerThread(worker_function)
            self.worker.output.connect(self.append_log)
            self.worker.start()
            
            # 在线程完成时更新文件路径
            def update_file_path():
                self.current_deleted_torrents_file = self.worker.function()
            self.worker.finished.connect(update_file_path)
            
        except Exception as e:
            self.append_log(f"发生错误: {str(e)}")

    def delete_deleted(self):
        """删除被站点删除的种子"""
        if not self.current_deleted_torrents_file:
            QMessageBox.warning(self, "警告", "请先检查站点删除的种子！")
            return
            
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这些被站点删除的种子吗？\n这将同时删除种子文件！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.log_output.clear()
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                def worker_function():
                    delete_site_deleted_torrents(self.current_deleted_torrents_file, config["local_server"])
                
                self.worker = WorkerThread(worker_function)
                self.worker.output.connect(self.append_log)
                self.worker.start()
            except Exception as e:
                self.append_log(f"发生错误: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 确保配置文件存在
        ensure_config_exists()
        self.setWindowTitle("qBittorrent Batch Cleaner")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        self.current_deleted_torrents_file = None

    def setup_ui(self):
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 设置按钮
        settings_btn = QPushButton("设置")
        settings_btn.setIcon(QIcon.fromTheme("configure"))
        settings_btn.clicked.connect(self.show_settings)
        layout.addWidget(settings_btn)
        
        # 远程功能区域
        remote_group = QWidget()
        remote_layout = QVBoxLayout(remote_group)
        remote_layout.setSpacing(10)
        
        remote_title = QLabel("远程种子管理")
        remote_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2a82da; margin-bottom: 5px;")
        remote_layout.addWidget(remote_title)
        
        remote_buttons = QHBoxLayout()
        
        # 检查本地种子按钮
        check_local_btn = QPushButton("检查本地待迁移种子")
        check_local_btn.setToolTip("检查本地下载器中未下载且带特定标签的种子，这些种子可能在远程下载器中")
        check_local_btn.clicked.connect(self.check_local)
        
        # 检查远程按钮（调试模式）
        check_remote_btn = QPushButton("检查远程种子")
        check_remote_btn.setToolTip("在远程下载器中查找对应的种子")
        check_remote_btn.clicked.connect(lambda: self.delete_remote(True))
        
        # 删除远程按钮
        delete_remote_btn = QPushButton("删除远程种子")
        delete_remote_btn.setToolTip("删除远程下载器中的对应种子，以便本地下载")
        delete_remote_btn.clicked.connect(lambda: self.delete_remote(False))
        
        remote_buttons.addWidget(check_local_btn)
        remote_buttons.addWidget(check_remote_btn)
        remote_buttons.addWidget(delete_remote_btn)
        remote_layout.addLayout(remote_buttons)
        layout.addWidget(remote_group)
        
        # 站点删种功能区域
        site_group = QWidget()
        site_layout = QVBoxLayout(site_group)
        site_layout.setSpacing(10)
        
        site_title = QLabel("站点删种功能")
        site_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2a82da; margin-bottom: 5px;")
        site_layout.addWidget(site_title)
        
        site_buttons = QHBoxLayout()
        
        # 检查站点删除按钮
        check_deleted_btn = QPushButton("检查站点删除")
        check_deleted_btn.clicked.connect(self.check_deleted)
        
        # 删除站点删除的种子按钮
        delete_deleted_btn = QPushButton("删除站点删除的种子")
        delete_deleted_btn.clicked.connect(self.delete_deleted)
        
        site_buttons.addWidget(check_deleted_btn)
        site_buttons.addWidget(delete_deleted_btn)
        site_layout.addLayout(site_buttons)
        layout.addWidget(site_group)
        
        # 添加分隔线
        def add_separator():
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            line.setStyleSheet("background-color: #424242;")
            return line
        
        # 在每个分组之间添加分隔线
        # layout.addWidget(add_separator())
        layout.addWidget(add_separator())
        
        # 日志输出区域
        log_group = QWidget()
        log_layout = QVBoxLayout(log_group)
        log_layout.setSpacing(5)
        
        log_title = QLabel("运行日志")
        log_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2a82da; margin-bottom: 5px;")
        log_layout.addWidget(log_title)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)
        
        layout.addWidget(log_group)

    def show_settings(self):
        dialog = ConfigDialog(self)
        dialog.exec()

    def append_log(self, text):
        self.log_output.append(text)
        # 滚动到底部
        self.log_output.verticalScrollBar().setValue(
            self.log_output.verticalScrollBar().maximum()
        )

    def check_local(self):
        self.log_output.clear()
        self.worker = WorkerThread(check_local_torrents)
        self.worker.output.connect(self.append_log)
        self.worker.start()

    def delete_remote(self, debug_mode):
        self.log_output.clear()
        self.worker = WorkerThread(delete_remote_torrents, debug_mode)
        self.worker.output.connect(self.append_log)
        self.worker.start()

    def check_deleted(self):
        """检查被站点删除的种子"""
        self.log_output.clear()
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            
            def worker_function():
                return check_deleted_torrents(config["local_server"])
            
            self.worker = WorkerThread(worker_function)
            self.worker.output.connect(self.append_log)
            self.worker.start()
            
            # 在线程完成时更新文件路径
            def update_file_path():
                self.current_deleted_torrents_file = self.worker.function()
            self.worker.finished.connect(update_file_path)
            
        except Exception as e:
            self.append_log(f"发生错误: {str(e)}")

    def delete_deleted(self):
        """删除被站点删除的种子"""
        if not self.current_deleted_torrents_file:
            QMessageBox.warning(self, "警告", "请先检查站点删除的种子！")
            return
            
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这些被站点删除的种子吗？\n这将同时删除种子文件！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.log_output.clear()
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                def worker_function():
                    delete_site_deleted_torrents(self.current_deleted_torrents_file, config["local_server"])
                
                self.worker = WorkerThread(worker_function)
                self.worker.output.connect(self.append_log)
                self.worker.start()
            except Exception as e:
                self.append_log(f"发生错误: {str(e)}")

def main():
    app = QApplication(sys.argv)
    
    # 设置深色主题
    set_dark_theme(app)
    
    # 设置应用程序范围的字体
    font = QFont("Microsoft YaHei UI", 9)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 