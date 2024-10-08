import socket
import time
import serial
import threading
import queue
from mpu6050 import mpu6050
import MPU6050filter
import numpy as np
import cv2
import io
import struct


# 定义常量
LOBOT__FRAME_HEADER = 0x55
LOBOT_CMD_ACTION_GROUP_RUN = 6

# 初始化串口，波特率为9600
serialHandle = serial.Serial("/dev/ttyS0", 9600)

# 创建一个线程队列用于传递姿态角
myQueue = queue.Queue()

# 定义一个标志位，控制是否测量偏航角
measure_yaw = False

# MPU6050传感器线程
def t_mpu6050():
    global measure_yaw
    sensor = mpu6050(address=0x68)
    sensor.set_gyro_range(mpu6050.GYRO_RANGE_2000DEG)
    sensor.set_accel_range(mpu6050.ACCEL_RANGE_16G)
    time.sleep(0.05)

    yaw_list = []

    while True:
        if measure_yaw:
            accel_data = sensor.get_accel_data()
            gyro_data = sensor.get_gyro_data()

            # 转换为 pitch, roll, yaw
            rotation = MPU6050filter.IMUupdate(accel_data['x'], accel_data['y'], accel_data['z'],
                                               gyro_data['x'], gyro_data['y'], gyro_data['z'])

            _, _, yaw = rotation

            yaw_list.append(yaw)

            if len(yaw_list) == 10:
                avg_yaw = sum(yaw_list) / len(yaw_list)
                yaw_list.clear()  # 清空列表以准备下一组数据

                # 将平均yaw值放入队列
                if myQueue.empty():
                    myQueue.put(avg_yaw)

            time.sleep(0.1)  # 调整采样间隔为100ms
        else:
            time.sleep(0.1)  # 如果不测量，则保持线程睡眠，避免CPU占用

# 运行动作组
def setGroupRun(group_id, group_count):
    buf = bytearray(b'\x55\x55')  # 帧头
    buf.append(5)  # 数据长度
    buf.append(LOBOT_CMD_ACTION_GROUP_RUN)  # 指令
    buf.append(group_id)  # 动作组id
    count_list = list(group_count.to_bytes(2, 'little'))
    buf.append(count_list[0])    # 次数
    buf.append(count_list[1])

    serialHandle.write(buf)

def connect():
    HOST = '192.168.137.125'  # 公网IP
    PORT = 1178
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect((HOST, PORT))
    return sock

def test(status):
    global measure_yaw
    status = int(status)
    
    if status == 0:
        print("停止")
        setGroupRun(0, 1)
        measure_yaw = False  # 停止测量偏航角
        
    elif status == 1:
        print("前进")
        measure_yaw = True  # 启动测量偏航角
        
        # 从队列获取最新的yaw平均值
        if not myQueue.empty():
            avg_yaw = myQueue.get()
            print(f"Average Yaw: {avg_yaw}")

            if avg_yaw > 10:
                setGroupRun(6, 1)
            elif avg_yaw < -10:
                setGroupRun(7, 1)
            else:
                setGroupRun(1, 1)
                
    elif status in [2, 3, 4, 5, 6, 7, 8, 9]:
        print(f"处理状态: {status}")
        measure_yaw = False  # 暂停测量偏航角，避免对其他动作影响
        # 执行相应动作组
        group_map = {
            2: 2,  # 前右
            3: 2,  # 右转
            4: 2,  # 右后
            5: 3,  # 后退
            6: 3,  # 左后
            7: 4,  # 左转
            8: 4,
            9: 20# 前左
        }
        setGroupRun(group_map[status], 1)

def action_control_loop():
    # 创建并启动MPU6050线程
    t1 = threading.Thread(target=t_mpu6050)
    t1.start()

    while True:
        sock = connect()
        status = sock.recv(1).decode()
        test(status)
        sock.close()

    t1.join()

# 视频流传输类
class VideoStreaming(object):
    def __init__(self, host, port):
        self.server_socket = socket.socket()  # 获取socket实例
        self.server_socket.bind((host, port))  # 绑定主机IP地址和端口号
        self.server_socket.listen(5)  # 设置监听数量

        print(" ")
        print("Host:", host)
        print("等待客服端连接...")
        print(" ")

        self.connection, self.client_address = self.server_socket.accept()  # 等待Client连接
        self.connect = self.connection.makefile('wb')  # 创建传输文件
        self.host_name = socket.gethostname()  # 获得服务端主机名
        self.host_ip = socket.gethostbyname(self.host_name)  # 获得服务端主机IP地址
        time.sleep(3)

    def connecting(self):
        print('等待连接')
        self.connection, self.client_address = self.server_socket.accept()  # 等待Client连接
        self.connect = self.connection.makefile('wb')  # 创建传输文件
        self.host_name = socket.gethostname()  # 获得服务端主机名
        self.host_ip = socket.gethostbyname(self.host_name)  # 获得服务端主机IP地址
        print('连接成功')

    def start(self) -> None:
        """开始传输视频流"""
        print("客服端已连接：")
        print("Client Host Name:", self.host_name)
        print("Connection from: ", self.client_address)
        print("Streaming...")
        self.stream = io.BytesIO()  # 创建一个io流，用于存放二进制数据

    def send(self, _img: cv2.typing.MatLike) -> bool:
        """发送图像数据"""
        try:
            try:
                img_encode = cv2.imencode('.jpg', _img)[1]  # 编码
            except:
                print('没有读取到图像')
                return False
            data_encode = np.array(img_encode)  # 将编码数据转换成二进制数据
            self.stream.write(data_encode)  # 将二进制数据存放到io流
            self.connect.write(struct.pack('<L', self.stream.tell()))  # 发送帧头数据
            self.connect.flush()  # 刷新发送
            self.stream.seek(0)  # 更新io流
            self.connect.write(self.stream.read())  # 发送图像数据
            self.stream.seek(0)  # 重置指针
            self.stream.truncate()  # 清空流

            self.connect.write(struct.pack('<L', 0))  # 发送帧尾
            return True
        except ConnectionResetError:
            print('连接已重置')
            self.connecting()
            return False

def video_streaming_loop():
    host = '192.168.137.116'  # 发送端IP地址
    port = 8000

    cap = cv2.VideoCapture(0)
    streamer = VideoStreaming(host, port)
    streamer.start()

    while True:
        ret, frame = cap.read()
        if not streamer.send(frame):
            break

if __name__ == '__main__':
    # 创建两个线程分别运行视频传输和动作控制
    video_thread = threading.Thread(target=video_streaming_loop)
    action_thread = threading.Thread(target=action_control_loop)

    video_thread.start()
    action_thread.start()

    video_thread.join()
    action_thread.join()
   