import ctypes
import cv2
import numpy as np
import os
import time
from typing import List, Optional

class MuMuCap:
    """
    MuMu模拟器截图工具类
    
    该类提供了对MuMu模拟器的截图功能，通过调用模拟器的DLL接口实现。
    主要功能包括：
    1. 连接模拟器实例
    2. 获取模拟器窗口大小
    3. 截取模拟器画面
    4. 将截图转换为OpenCV格式
    
    使用示例：
    ```python
    # 创建截图实例
    cap = MuMuCap(0, r"L:\MuMuPlayer-12.0")
    
    # 获取截图
    image = cap.screencap()
    
    # 显示图片
    cv2.imshow("Screenshot", image)
    cv2.waitKey(0)
    ```
    """
    
    def __init__(
            self,
            instance_index: int,
            emulator_install_path: str,
            display_id: int = 0,
            fps: int = 15
    ):
        """
        初始化MuMu模拟器截图工具
        
        Args:
            instance_index (int): 模拟器实例的编号，通常为0
            emulator_install_path (str): 模拟器安装路径，例如 r"L:\MuMuPlayer-12.0"
            display_id (int, optional): 显示窗口ID，默认为0
            fps (int, optional): 截图最大帧率，默认为15
        """
        
        self.display_id = display_id
        self.instance_index = instance_index
        self.emulator_install_path = emulator_install_path
        self.fps = fps
        self.last_capture_time = 0  # 上次截图时间
        
        # DLL文件路径
        self.dll_path = os.path.join(self.emulator_install_path, "shell/sdk/external_renderer_ipc.dll")
        if not os.path.exists(self.dll_path):
            self.dll_path = os.path.join(self.emulator_install_path, "nx_main/sdk/external_renderer_ipc.dll")
        if not os.path.exists(self.dll_path):
            print(f"无法找到DLL文件: {self.dll_path}")
            # raise FileNotFoundError(f"无法找到DLL文件: {self.dll_path}")

        # 初始化DLL接口
        self._init_dll()
        
        # 连接模拟器并获取显示信息
        self.handle = self._connect()
        self._get_display_info()
        
    def _init_dll(self):
        """初始化DLL接口，设置函数参数类型和返回类型"""
        self.nemu = ctypes.CDLL(self.dll_path)
        
        # 设置connect函数的参数类型和返回类型
        self.nemu.nemu_connect.restype = ctypes.c_int
        self.nemu.nemu_connect.argtypes = [ctypes.c_wchar_p, ctypes.c_int]
        
        # 设置disconnect函数的参数类型
        self.nemu.nemu_disconnect.argtypes = [ctypes.c_int]
        
        # 设置capture_display函数的参数类型和返回类型
        self.nemu.nemu_capture_display.restype = ctypes.c_int
        self.nemu.nemu_capture_display.argtypes = [
            ctypes.c_int,      # handle
            ctypes.c_uint,     # display_id
            ctypes.c_int,      # buffer_size
            ctypes.POINTER(ctypes.c_int),  # width
            ctypes.POINTER(ctypes.c_int),  # height
            ctypes.POINTER(ctypes.c_ubyte),  # pixels
        ]
        
    def _connect(self) -> int:
        """
        连接模拟器实例
        
        Returns:
            int: 模拟器句柄
            
        Raises:
            Exception: 连接失败时抛出异常
        """
        handle = self.nemu.nemu_connect(self.emulator_install_path, self.instance_index)
        if handle == 0:
            print(f"连接模拟器失败")
            # raise Exception("连接模拟器失败")
        return handle
        
    def _get_display_info(self):
        """获取模拟器窗口大小信息"""
        width = ctypes.c_int(0)
        height = ctypes.c_int(0)
        
        # 获取窗口大小
        result = self.nemu.nemu_capture_display(
            self.handle,
            self.display_id,
            0,
            ctypes.byref(width),
            ctypes.byref(height),
            None,
        )
        
        if result != 0:
            print(f"获取窗口大小失败")
            # raise Exception("获取窗口大小失败")
            
        self.width = width.value
        self.height = height.value
        self.buffer_size = self.width * self.height * 4
        self.pixels = (ctypes.c_ubyte * self.buffer_size)()
        
    def _buffer_to_opencv(self) -> cv2.Mat:
        """
        将像素缓冲区转换为OpenCV图像格式
        
        Returns:
            cv2.Mat: OpenCV格式的图像
        """
        # 将像素数据转换为numpy数组并重塑为图像格式
        pixel_array = np.frombuffer(self.pixels, dtype=np.uint8).reshape((self.height, self.width, 4))
        # 转换颜色空间从RGBA到RGB，并翻转图像
        return cv2.cvtColor(pixel_array[::-1, :, [2, 1, 0]], cv2.COLOR_RGBA2RGB)
        
    def screencap(self, region: Optional[List[int]] = None) -> cv2.Mat:
        """
        截取模拟器画面，并根据设置的帧率控制截图频率
        
        Args:
            region (Optional[List[int]], optional): 截图区域 [x, y, w, h]，默认为None表示截取整个画面
        
        Returns:
            cv2.Mat: OpenCV格式的截图
            
        Raises:
            BufferError: 截图失败时抛出异常
        """
        current_time = time.time()
        min_interval = 1.0 / self.fps
        
        # 计算距离上次截图的时间间隔
        elapsed = current_time - self.last_capture_time
        
        # 如果时间间隔小于所需的最小间隔，则等待
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        
        # 更新上次截图时间
        self.last_capture_time = time.time()
        
        result = self.nemu.nemu_capture_display(
            self.handle,
            self.display_id,
            self.buffer_size,
            ctypes.c_int(self.width),
            ctypes.c_int(self.height),
            self.pixels,
        )
        
        if result > 1:
            return None
            raise BufferError("截图失败")
            
        # 获取完整图像
        full_image = self._buffer_to_opencv()
        
        # 如果指定了区域，则截取对应区域
        if region is not None:
            try:
                x, y, w, h = region
                # 确保坐标在有效范围内
                x = max(0, min(x, self.width - 1))
                y = max(0, min(y, self.height - 1))
                w = min(w, self.width - x)
                h = min(h, self.height - y)
                
                # 截取区域
                return full_image[y:y+h, x:x+w]
            except Exception:
                # 如果截取失败，返回完整图像
                return full_image
                
        return full_image
    
    def set_fps(self, fps: int):
        """
        设置截图的最大帧率
        
        Args:
            fps (int): 每秒截图次数上限
        """
        self.fps = fps
        
    def __del__(self):
        """析构函数，断开与模拟器的连接"""
        if hasattr(self, 'nemu') and hasattr(self, 'handle'):
            self.nemu.nemu_disconnect(self.handle)


if __name__ == '__main__':
    # 使用示例
    import time
    
    # 创建截图实例
    cap = MuMuCap(2, r"L:\MuMuPlayer-12.0")
    
    # 测试截图性能
    start_time = time.time()
    image = cap.screencap()
    print(f"截图耗时: {time.time() - start_time:.3f}秒")
    
    # 显示截图
    # cv2.imshow("MuMu模拟器截图", image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    cv2.imwrite("./imgs/screenshot.png", image)