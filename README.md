# qBittorrent Batch Cleaner

一个用于批量清理 qBittorrent 种子的工具集。包含本地种子检查和远程种子删除功能。

## 功能特点

- 支持检查本地 qBittorrent 服务器中的种子
- 支持同时删除多个远程 qBittorrent 服务器中的种子
- 支持按标签和分类筛选种子
- 提供调试模式，可以在删除前预览要删除的种子
- 详细的日志记录功能
- 多线程并行处理，提高效率

## 使用要求

- Python 3.6+
- qbittorrent-api

## 安装

1. 克隆仓库：

    ```bash
    git clone https://github.com/yourusername/qbittorrent-batch-cleaner.git
    cd qbittorrent-batch-cleaner
    ```

2. 安装依赖：

    ```bash
    pip install qbittorrent-api
    ```

3. 创建配置文件 `config.json`：

    ```json
    {
        "local_server": {
            "url": "http://localhost:8080",
            "username": "admin",
            "password": "adminadmin",
            "tag": "要删除的标签",
            "category": "要删除的分类（可选）"
        },
        "remote_servers": [
            {
                "name": "服务器1",
                "url": "http://server1:8080",
                "username": "admin",
                "password": "adminadmin"
            },
            {
                "name": "服务器2",
                "url": "http://server2:8080",
                "username": "admin",
                "password": "adminadmin"
            }
        ]
    }
    ```

## 使用方法

1. 检查本地种子：

    ```bash
    python check_local_torrents.py
    ```

    此命令会检查本地服务器中符合条件的种子，并生成 `torrents_to_delete.json` 文件。

2. 删除远程种子：

    ```bash
    # 调试模式（只检查不删除）
    python delete_remote_torrents.py --debug

    # 执行删除
    python delete_remote_torrents.py
    ```

## 日志记录

- 文本日志保存在 `logs/delete_log.txt`
- JSON格式的详细记录保存在 `logs/delete_records.json`

## 注意事项

- 删除操作不可恢复，请谨慎使用
- 建议先使用调试模式（--debug）检查要删除的种子
- 确保配置文件中的服务器信息正确

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
