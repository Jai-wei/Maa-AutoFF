# 获取所有MuMu模拟器实例的信息
import os
import subprocess
import json

class Get_emulators_list:
    def __init__(self, MuMu_path=r'L:\MuMuPlayer-12.0'):
        self.MuMu_path = MuMu_path

        shell_dir = os.path.join(self.MuMu_path, "shell")
        # MuMu模拟器5
        nx_main_dir = os.path.join(self.MuMu_path, "nx_main")

        if os.path.exists(shell_dir) and os.path.isdir(shell_dir):
            self.shell_path = shell_dir
        elif os.path.exists(nx_main_dir) and os.path.isdir(nx_main_dir):
            self.shell_path = nx_main_dir
        else:
            print(f"无法找到MuMu模拟器的shell文件夹: {shell_dir} or {nx_main_dir}")
            raise FileNotFoundError(f"无法找到MuMu模拟器的shell文件夹: {shell_dir} or {nx_main_dir}")

        self.mumu_manager = os.path.join(self.shell_path, 'MuMuManager.exe')

    def get_mumu_list(self):
        """
        获取所有MuMu模拟器实例的信息
        :return: 包含模拟器信息的列表
        """
        try:
            # 设置Qt插件路径环境变量，确保子进程能找到必要的Qt插件
            env = os.environ.copy()
            qt_plugin_path = os.path.join(self.MuMu_path, 'shell', 'plugins')

            # MuMu模拟器5
            if not os.path.exists(qt_plugin_path):
                qt_plugin_path = os.path.join(self.MuMu_path, 'nx_main', 'plugins')
            
            if 'QT_PLUGIN_PATH' not in env:
                env['QT_PLUGIN_PATH'] = qt_plugin_path
            else:
                env['QT_PLUGIN_PATH'] = f"{qt_plugin_path};{env['QT_PLUGIN_PATH']}"
            
            # 使用subprocess执行命令，不显示命令行窗口
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            # 执行命令获取模拟器信息，使用UTF-8编码
            result = subprocess.run(
                [self.mumu_manager, 'info', '-v', 'all'],
                capture_output=True,
                encoding='utf-8',
                errors='ignore',  # 忽略无法解码的字符
                startupinfo=startupinfo,
                env=env
            )

            if result.returncode == 0 and result.stdout:
                # 解析输出信息
                emulators_info = []
                result_json = json.loads(result.stdout)

                # 处理不同格式的返回结果
                # 检查是否为单个模拟器的情况（没有嵌套的字典）
                if "index" in result_json:
                    # 单个模拟器的情况，将其转换为多个模拟器的格式
                    result_json = {result_json["index"]: result_json}
                    
                # 处理所有模拟器
                for item, value in result_json.items():
                    # 模拟器开启状态
                    if value['is_process_started'] == True:
                        json_cash = {'状态': 'M-开启', '编号': int(value['index']), '名称': value['name'], 'ADB': f"{value['adb_host_ip']}:{value['adb_port']}"}
                    else:
                        json_cash = {'状态': 'M-关闭', '编号': int(value['index']), '名称': value['name']}
                    emulators_info.append(json_cash)
                return emulators_info
            else:
                error_msg = result.stderr if result.stderr else "未知错误"
                print(f"获取模拟器信息失败: {error_msg}")
                return []

        except Exception as e:
            print(f"执行命令时发生错误: {str(e)}")
            return []


if __name__ == '__main__':
    get_emulators_list = Get_emulators_list()
    result = get_emulators_list.get_mumu_list()
    print("模拟器列表：")
    print(json.dumps(result, ensure_ascii=False, indent=2))

