"""
设置API模块，提供给前端调用的设置相关接口
"""
import os
import logging
import webview
from .settings_manager import settings_manager

# 配置日志
logger = logging.getLogger(__name__)

class SettingsAPI:
    """
    设置API类，提供给前端调用的设置相关接口
    """
    def __init__(self):
        """初始化设置API"""
        self.window = None
    
    def set_window(self, window):
        """设置窗口引用"""
        self.window = window
    
    def get_all_settings(self):
        """获取所有设置"""
        try:
            settings = settings_manager.get_settings()
            logger.info("获取所有设置成功")
            return {
                "success": True,
                "data": settings
            }
        except Exception as e:
            logger.error(f"获取所有设置失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_setting(self, key, value):
        """更新单个设置项"""
        try:
            result = settings_manager.update_setting(key, value)
            if result:
                logger.info(f"更新设置成功: {key}={value}")
                return {
                    "success": True,
                    "message": f"设置 {key} 已更新"
                }
            else:
                logger.warning(f"更新设置失败: {key}={value}")
                return {
                    "success": False,
                    "error": "更新设置失败"
                }
        except Exception as e:
            logger.error(f"更新设置出错: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_settings(self, settings_dict):
        """批量更新多个设置项"""
        try:
            result = settings_manager.update_settings(settings_dict)
            if result:
                logger.info(f"批量更新设置成功: {settings_dict}")
                return {
                    "success": True,
                    "message": "设置已更新"
                }
            else:
                logger.warning(f"批量更新设置失败: {settings_dict}")
                return {
                    "success": False,
                    "error": "更新设置失败"
                }
        except Exception as e:
            logger.error(f"批量更新设置出错: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def select_directory(self, validate_shell=False):
        """
        打开目录选择对话框
        
        参数:
            validate_shell: 是否验证选择的目录下是否存在shell文件夹
        """
        try:
            if self.window:
                directory = self.window.create_file_dialog(
                    webview.FOLDER_DIALOG
                )
                if directory and len(directory) > 0:
                    selected_dir = directory[0]
                    logger.info(f"选择目录: {selected_dir}")
                    
                    # 如果需要验证shell文件夹
                    if validate_shell:
                        shell_dir = os.path.join(selected_dir, "shell")
                        # MuMu模拟器5
                        nx_main_dir = os.path.join(selected_dir, "nx_main")
                        has_shell = os.path.exists(shell_dir) and os.path.isdir(shell_dir) or os.path.exists(nx_main_dir) and os.path.isdir(nx_main_dir)
                        return {
                            "success": True,
                            "data": selected_dir,
                            "has_shell": has_shell
                        }
                    else:
                        return {
                            "success": True,
                            "data": selected_dir
                        }
                else:
                    logger.info("用户取消选择目录")
                    return {
                        "success": False,
                        "error": "未选择目录"
                    }
            else:
                logger.error("窗口引用未设置")
                return {
                    "success": False,
                    "error": "窗口引用未设置"
                }
        except Exception as e:
            logger.error(f"选择目录出错: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# 创建全局设置API实例
settings_api = SettingsAPI() 