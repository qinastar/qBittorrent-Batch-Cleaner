from qbittorrentapi import Client
import json
import datetime
import os
import sys
import io
import codecs
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# 设置控制台输出编码为UTF-8
if sys.platform.startswith('win'):
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    except (AttributeError, io.UnsupportedOperation):
        pass

def format_size(size_bytes):
    """将字节大小转换为人类可读的格式"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            if not isinstance(config, dict):
                raise ValueError("配置文件格式错误：根对象必须是字典类型")
            return config
    except json.JSONDecodeError as e:
        raise ValueError(f"配置文件JSON格式错误: {str(e)}")
    except FileNotFoundError:
        raise FileNotFoundError("找不到配置文件 config.json")

def create_log_directory():
    if not os.path.exists("logs"):
        os.makedirs("logs")

def check_deleted_torrents(local_config, selected_servers, remote_servers):
    """检查被站点删除的种子"""
    try:
        deleted_torrents = []
        total_size = 0
        lock = threading.Lock()
        
        def process_server(server_config, is_local=False):
            nonlocal total_size
            server_name = "本地服务器" if is_local else server_config["name"]
            
            try:
                print(f"\n正在连接服务器: {server_name}")
                
                # 连接qBittorrent
                qb = Client(
                    host=server_config["url"],
                    username=server_config["username"],
                    password=server_config["password"]
                )
                
                server_deleted = []
                server_size = 0
                
                try:
                    qb.auth_log_in()
                    with lock:
                        print(f"已成功连接到服务器 {server_name}")
                    
                    print(f"正在获取服务器 {server_name} 的种子列表...")
                    torrents = qb.torrents_info()
                    
                    print(f"正在检查服务器 {server_name} 的种子状态...")
                    for torrent in torrents:
                        trackers = qb.torrents_trackers(torrent.hash)
                        is_deleted = False
                        
                        for tracker in trackers:
                            if isinstance(tracker, dict) and "msg" in tracker:
                                msg = tracker.get("msg", "").lower()
                                if "torrent not found" in msg or "torrent not exists" in msg or "unregistered torrent" in msg:
                                    is_deleted = True
                                    break
                        
                        if is_deleted:
                            # 为种子添加标签
                            current_tags = torrent.tags.split(",") if torrent.tags else []
                            if "站点删种" not in current_tags:
                                new_tags = current_tags + ["站点删种"]
                                qb.torrents_add_tags(tags="站点删种", torrent_hashes=torrent.hash)
                            
                            server_deleted.append({
                                "name": torrent.name,
                                "hash": torrent.hash,
                                "size": torrent.size,
                                "tracker_msg": msg,
                                "server": server_name
                            })
                            server_size += torrent.size
                    
                    with lock:
                        if server_deleted:
                            deleted_torrents.extend(server_deleted)
                            total_size += server_size
                            print(f"\n在服务器 {server_name} 上找到 {len(server_deleted)} 个被站点删除的种子")
                            print(f"服务器 {server_name} 总大小: {format_size(server_size)}")
                        else:
                            print(f"\n在服务器 {server_name} 上未找到被站点删除的种子")
                    
                except Exception as e:
                    with lock:
                        print(f"处理服务器 {server_name} 时发生错误: {str(e)}")
                finally:
                    qb.auth_log_out()
                    
            except Exception as e:
                with lock:
                    print(f"连接服务器 {server_name} 时发生错误: {str(e)}")
        
        # 使用线程池处理所有选中的服务器
        with ThreadPoolExecutor() as executor:
            futures = []
            
            # 处理本地服务器
            if "local" in selected_servers:
                futures.append(executor.submit(process_server, local_config, True))
            
            # 处理远程服务器
            for server in remote_servers:
                if server["name"] in selected_servers:
                    futures.append(executor.submit(process_server, server))
            
            # 等待所有任务完成
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"处理服务器时发生错误: {str(e)}")
        
        if deleted_torrents:
            # 创建日志目录
            create_log_directory()
            
            # 保存删除种子列表
            current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = f"logs/deleted_torrents_{current_time}.json"
            
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump({
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_torrents": len(deleted_torrents),
                    "total_size": total_size,
                    "torrents": deleted_torrents
                }, f, ensure_ascii=False, indent=4)
            
            # 打印总结
            print(f"\n=== 总结 ===")
            print(f"所有服务器共找到 {len(deleted_torrents)} 个被站点删除的种子")
            print(f"总大小: {format_size(total_size)}")
            print("\n种子列表:")
            for idx, torrent in enumerate(deleted_torrents, 1):
                print(f"{idx}. [{torrent['server']}] {torrent['name']} (大小: {format_size(torrent['size'])})")
                print(f"   Tracker消息: {torrent['tracker_msg']}")
            
            print(f"\n种子列表已保存至: {json_file}")
            return json_file
        else:
            print("\n未找到被站点删除的种子")
            return None
            
    except Exception as e:
        print(f"程序执行过程中发生错误: {str(e)}")
        return None

def delete_site_deleted_torrents(json_file_path, local_config, selected_servers, remote_servers):
    """删除被站点删除的种子及其文件"""
    if not os.path.exists(json_file_path):
        print(f"找不到种子列表文件: {json_file_path}")
        return
    
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            torrents = data.get("torrents", [])
        
        if not torrents:
            print("没有需要删除的种子")
            return
        
        # 按服务器分组种子
        torrents_by_server = {}
        for torrent in torrents:
            server_name = torrent["server"]
            if server_name not in torrents_by_server:
                torrents_by_server[server_name] = []
            torrents_by_server[server_name].append(torrent)
        
        lock = threading.Lock()
        total_deleted = 0
        total_size = 0
        
        def process_server_deletion(server_config, server_torrents, is_local=False):
            nonlocal total_deleted, total_size
            server_name = "本地服务器" if is_local else server_config["name"]
            
            try:
                print(f"\n正在连接服务器: {server_name}")
                qb = Client(
                    host=server_config["url"],
                    username=server_config["username"],
                    password=server_config["password"]
                )
                
                try:
                    qb.auth_log_in()
                    with lock:
                        print(f"已成功连接到服务器 {server_name}")
                    
                    print(f"正在删除服务器 {server_name} 的种子...")
                    server_deleted = 0
                    server_size = 0
                    
                    for torrent in server_torrents:
                        try:
                            qb.torrents_delete(delete_files=True, torrent_hashes=torrent["hash"])
                            with lock:
                                print(f"已删除: [{server_name}] {torrent['name']} (大小: {format_size(torrent['size'])})")
                            server_deleted += 1
                            server_size += torrent["size"]
                        except Exception as e:
                            with lock:
                                print(f"删除种子 {torrent['name']} 时发生错误: {str(e)}")
                    
                    with lock:
                        total_deleted += server_deleted
                        total_size += server_size
                        print(f"\n服务器 {server_name} 删除完成！")
                        print(f"共删除 {server_deleted} 个种子")
                        print(f"释放空间: {format_size(server_size)}")
                    
                except Exception as e:
                    with lock:
                        print(f"处理服务器 {server_name} 时发生错误: {str(e)}")
                finally:
                    qb.auth_log_out()
                    
            except Exception as e:
                with lock:
                    print(f"连接服务器 {server_name} 时发生错误: {str(e)}")
        
        # 使用线程池处理所有选中的服务器
        with ThreadPoolExecutor() as executor:
            futures = []
            
            # 处理本地服务器
            if "local" in selected_servers and "本地服务器" in torrents_by_server:
                futures.append(executor.submit(
                    process_server_deletion,
                    local_config,
                    torrents_by_server["本地服务器"],
                    True
                ))
            
            # 处理远程服务器
            for server in remote_servers:
                if server["name"] in selected_servers and server["name"] in torrents_by_server:
                    futures.append(executor.submit(
                        process_server_deletion,
                        server,
                        torrents_by_server[server["name"]]
                    ))
            
            # 等待所有任务完成
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"处理服务器时发生错误: {str(e)}")
        
        print(f"\n=== 总结 ===")
        print(f"所有服务器共删除 {total_deleted} 个种子")
        print(f"总释放空间: {format_size(total_size)}")
            
    except Exception as e:
        print(f"程序执行过程中发生错误: {str(e)}")

if __name__ == "__main__":
    try:
        config = load_config()
        json_file = check_deleted_torrents(config["local_server"], ["local"], [])
        if json_file and input("\n是否删除这些种子？(y/N) ").lower() == 'y':
            delete_site_deleted_torrents(json_file, config["local_server"], ["local"], [])
    except Exception as e:
        print(f"程序执行过程中发生错误: {str(e)}") 