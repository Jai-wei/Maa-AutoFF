import ctypes
import subprocess
import time
from typing import List, Tuple
from abc import ABC, abstractmethod
import os


class Touch(ABC):
    """触摸操作抽象基类"""
    @abstractmethod
    def click(self, x: int, y: int, duration: int = 100, clicks: int = 1):
        """
        点击某个坐标点
        :param x: x坐标
        :param y: y坐标
        :param duration: 持续时间(毫秒). 默认100ms
        :param clicks: 点击次数. 默认1次
        """
        pass

    @abstractmethod
    def swipe(self, points: List[Tuple[int, int]], duration: int = 500):
        """
        模拟手势(滑动)
        :param points: 坐标点列表 [(x1,y1), (x2,y2), ...]
        :param duration: 持续时间(毫秒). 默认500ms
        """
        pass


class CommandBuilder:
    """MaaTouch命令构建器"""
    def __init__(self):
        self._content = ""
        self._delay = 0

    def append(self, new_content):
        self._content += new_content + "\n"

    def commit(self):
        self.append("c")

    def wait(self, ms):
        self.append(f"w {ms}")
        self._delay += ms

    def up(self, contact_id):
        self.append(f"u {contact_id}")

    def down(self, contact_id, x, y, pressure):
        self.append(f"d {contact_id} {x} {y} {pressure}")

    def move(self, contact_id, x, y, pressure):
        self.append(f"m {contact_id} {x} {y} {pressure}")

    def publish(self, connection):
        self.commit()
        connection._send_command(self._content)
        time.sleep(self._delay / 1000)
        self.reset()

    def reset(self):
        self._content = ""
        self._delay = 0


class MuMuApi:
    """MuMu模拟器API封装"""
    def __init__(self, dll_path: str):
        self.nemu = ctypes.CDLL(dll_path)
        self._setup_api_functions()

    def _setup_api_functions(self):
        # 连接相关
        self.nemu.nemu_connect.restype = ctypes.c_int
        self.nemu.nemu_connect.argtypes = [ctypes.c_wchar_p, ctypes.c_int]
        self.nemu.nemu_disconnect.argtypes = [ctypes.c_int]

        # 显示相关
        self.nemu.nemu_capture_display.restype = ctypes.c_int
        self.nemu.nemu_capture_display.argtypes = [
            ctypes.c_int, ctypes.c_uint, ctypes.c_int,
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_ubyte)
        ]

        # 触摸事件相关
        self.nemu.nemu_input_event_touch_down.restype = ctypes.c_int
        self.nemu.nemu_input_event_touch_down.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int
        ]
        self.nemu.nemu_input_event_touch_up.restype = ctypes.c_int
        self.nemu.nemu_input_event_touch_up.argtypes = [ctypes.c_int, ctypes.c_int]

    def connect(self, emulator_install_path: str, instance_index: int) -> int:
        res = self.nemu.nemu_connect(emulator_install_path, instance_index)
        if res == 0:
            print(f"连接模拟器失败")
            # raise Exception("连接模拟器失败")
        return res

    def disconnect(self, handle: int):
        self.nemu.nemu_disconnect(handle)

    def capture_display(self, handle: int, display_id: int, buffer_size: int,
                       width: ctypes.c_int, height: ctypes.c_int, pixels) -> int:
        return self.nemu.nemu_capture_display(
            handle, display_id, buffer_size, width, height, pixels
        )

    def input_event_touch_down(self, handle: int, display_id: int, x: int, y: int):
        res = self.nemu.nemu_input_event_touch_down(handle, display_id, x, y)
        if res > 0:
            print(f"触摸按下事件失败")
            # raise Exception("触摸按下事件失败")
        return res

    def input_event_touch_up(self, handle: int, display_id: int):
        res = self.nemu.nemu_input_event_touch_up(handle, display_id)
        if res > 0:
            print(f"触摸抬起事件失败")
            # raise Exception("触摸抬起事件失败")
        return res


class MouseController(Touch):
    """统一的鼠标控制器类，支持MaaTouch和MuMuTouch两种实现"""
    def __init__(self, emulator_type: str, **kwargs):
        """
        初始化鼠标控制器
        :param emulator_type: 模拟器类型，支持 'mumu' 或 'maa'
        :param kwargs: 其他参数
            mumu参数:
                - emulator_install_path: 模拟器安装路径
                - instance_index: 实例索引
                - display_id: 显示ID
            maa参数:
                - mumupath: 模拟器路径
                - serial: 设备序列号
        """
        self.emulator_type = emulator_type.lower()
        if self.emulator_type == 'mumu':
            self._init_mumu(**kwargs)
        elif self.emulator_type == 'maa':
            self._init_maa(**kwargs)
        else:
            print(f"不支持的模拟器类型")
            # raise ValueError("不支持的模拟器类型")

    def _init_mumu(self, emulator_install_path: str, instance_index: int, display_id: int = 0):
        """初始化MuMu模拟器"""
        self.display_id = display_id
        self.instance_index = instance_index
        self.emulator_install_path = emulator_install_path
        self.dll_path = os.path.join(self.emulator_install_path, "shell/sdk/external_renderer_ipc.dll")
        if not os.path.exists(self.dll_path):
            self.dll_path = os.path.join(self.emulator_install_path, "nx_main/sdk/external_renderer_ipc.dll")
        if not os.path.exists(self.dll_path):
            print(f"无法找到DLL文件: {self.dll_path}")

        self.width: int = 0
        self.height: int = 0

        self.nemu = MuMuApi(self.dll_path)
        self.handle = self.nemu.connect(self.emulator_install_path, self.instance_index)
        self._get_display_info()

    def _init_maa(self, mumupath: str, serial: str):
        """初始化MaaTouch模拟器"""
        self.mumupath = mumupath
        self.serial = serial
        self.adb_path = mumupath + r'/shell/adb.exe'
        if not os.path.exists(self.adb_path):
            self.adb_path = mumupath + r'/nx_main/adb.exe'
        self.maatouch_path = mumupath + r'/bin/maatouch'
        self.remote_path = "/data/local/tmp/maatouch"
        
        self._init_device()
        self._get_device_info()

    def _get_display_info(self):
        """获取MuMu显示信息"""
        width = ctypes.c_int(0)
        height = ctypes.c_int(0)
        result = self.nemu.capture_display(
            self.handle, self.display_id, 0,
            ctypes.byref(width), ctypes.byref(height), None
        )
        if result != 0:
            print(f"获取显示尺寸失败")
            # raise Exception("获取显示尺寸失败")
        self.width, self.height = width.value, height.value

    def _init_device(self):
        """初始化MaaTouch设备"""
        subprocess.run(
            [self.adb_path, '-s', self.serial, 'push', self.maatouch_path, self.remote_path],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        self.process = subprocess.Popen(
            [self.adb_path, '-s', self.serial, 'shell',
             f'CLASSPATH={self.remote_path} app_process / com.shxyke.MaaTouch.App'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        self._maatouch_stream = self.process.stdin

    def _get_device_info(self):
        """获取MaaTouch设备信息"""
        info = self.process.stdout.readline().decode().strip().split()
        _, self.max_contacts, self.max_x, self.max_y, self.max_pressure = info

    def _send_command(self, content):
        """发送MaaTouch命令"""
        self._maatouch_stream.write(content.encode("utf-8"))
        self._maatouch_stream.flush()

    def click(self, x: int, y: int, waittime: int = 0.1, duration: int = 100, clicks: int = 1):
        # print(f"点击操作: x={x}, y={y}, duration={duration}, clicks={clicks}")
        """点击操作"""
        for _ in range(clicks):
            if self.emulator_type == 'mumu':
                self.nemu.input_event_touch_down(self.handle, self.display_id, x, y)
                time.sleep(duration / 1000)
                self.nemu.input_event_touch_up(self.handle, self.display_id)
                if clicks > 1 and _ < clicks - 1:
                    time.sleep(0.1)  # 连续点击之间的间隔
            else:  # maa
                builder = CommandBuilder()
                builder.down(0, x, y, 100)
                if duration:
                    builder.wait(duration)
                builder.up(0)
                builder.publish(self)
                if clicks > 1 and _ < clicks - 1:
                    time.sleep(0.1)  # 连续点击之间的间隔
        time.sleep(waittime)

    def swipe(self, points: List[Tuple[int, int]], waittime: int = 0.1, duration: int = 500):
        """滑动操作"""
        # 如果points长度为2，则复制最后一个点使长度为3（防止滑动失效）
        if len(points) == 2:
            points = points + [points[-1]]
            
        if self.emulator_type == 'mumu':
            for point in points:
                x, y = point
                self.nemu.input_event_touch_down(self.handle, self.display_id, x, y)
                time.sleep(duration / len(points) / 1000)
            self.nemu.input_event_touch_up(self.handle, self.display_id)
        else:  # maa
            points = [list(map(int, point)) for point in points]
            builder = CommandBuilder()
            point_id = 0

            x, y = points.pop(0)
            builder.down(point_id, x, y, 100)
            builder.publish(self)

            for x, y in points:
                builder.move(point_id, x, y, 100)
                if duration:
                    builder.wait(duration / len(points))
                builder.commit()

            builder.publish(self)
            builder.up(point_id)
            builder.publish(self)
        time.sleep(waittime)

    def __del__(self):
        """清理资源"""
        if self.emulator_type == 'mumu':
            self.nemu.disconnect(self.handle)
        else:  # maa
            if hasattr(self, 'process'):
                self.process.terminate()


if __name__ == "__main__":
    # MuMu示例
    mumu = MouseController('mumu', emulator_install_path=r'L:\MuMuPlayer-12.0', instance_index=0)
    mumu.click(1000, 650, 100)
    mumu.swipe([(200, 570), (220, 570), (220, 570)], 2000)

    # MaaTouch示例
    maa = MouseController('maa', mumupath=r'L:\MuMuPlayer-12.0', serial="192.168.31.174:5555")
    maa.click(1000, 650, 100)
    maa.swipe([(200, 570), (220, 570), (220, 570)], 2000)
