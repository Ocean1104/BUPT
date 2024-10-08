#final_code

import socket
import time
import serial
import threading
import queue
from mpu6050 import mpu6050
import MPU6050filter

# 定义常量
LOBOT__FRAME_HEADER              = 0x55
LOBOT_CMD_SERVO_MOVE             = 3
LOBOT_CMD_ACTION_GROUP_RUN       = 6
LOBOT_CMD_ACTION_GROUP_STOP      = 7
LOBOT_CMD_ACTION_GROUP_SPEED     = 11
LOBOT_CMD_GET_BATTERY_VOLTAGE    = 15

# 初始化串口，波特率为9600
serialHandle = serial.Serial("/dev/ttyS0", 9600)

# 创建一个线程队列用于传递姿态角
myQueue = queue.Queue()

# 定义一个标志位，控制是否测量偏航角
measure_yaw = False

esp32_ip = "192.168.137.164."
esp32_port = 80

def receive_data_from_esp32(callback):
    while True:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print(f"Connecting to ESP32 at {esp32_ip}:{esp32_port}...")
            client_socket.connect((esp32_ip, esp32_port))
            print("Connected!")

            while True:
                try:
                    request = "GET / HTTP/1.1\r\nHost: {}\r\n\r\n".format(esp32_ip)
                    client_socket.sendall(request.encode())

                    data = client_socket.recv(1024)
                    if data:
                        # 假设status是简单的一个数字，你可以直接使用int转换
                        try:
                            status_str = data.decode('utf-8').strip()  # 清除可能的空白字符
                            status = int(status_str)  # 转换为整数
                            callback(status)  # 使用回调函数将 status 值传递出去
                        except ValueError:
                            print(f"Received data is not a valid integer: {data.decode('utf-8')}")
                    else:
                        print("No data received. Retrying...")
                        break

                except (socket.error, Exception) as e:
                    print(f"An error occurred while receiving data: {e}")
                    break

        except (socket.error, Exception) as e:
            print(f"An error occurred during connection: {e}")
            time.sleep(1)

        finally:
            client_socket.close()
            print("Connection closed. Reconnecting...")

def t_mpu6050():
    sensor = mpu6050(address=0x68)
    sensor.set_gyro_range(mpu6050.GYRO_RANGE_2000DEG)
    sensor.set_accel_range(mpu6050.ACCEL_RANGE_16G)
    time.sleep(0.05)

    yaw_list = []
    initial_yaw = 0

    while True:
        if measure_yaw:
            accel_data = sensor.get_accel_data()
            gyro_data = sensor.get_gyro_data()

            # 转换为 pitch, roll, yaw
            rotation = MPU6050filter.IMUupdate(accel_data['x'], accel_data['y'], accel_data['z'],
                                               gyro_data['x'], gyro_data['y'], gyro_data['z'])

            _, _, yaw = rotation

            # 计算相对偏航角
            relative_yaw = yaw - initial_yaw
            yaw_list.append(relative_yaw)

            if len(yaw_list) == 10:
                avg_yaw = sum(yaw_list) / len(yaw_list)
                yaw_list.clear()  # 清空列表以准备下一组数据

                # 将平均yaw值放入队列
                if myQueue.empty():
                    myQueue.put(avg_yaw)

            time.sleep(0.1)  # 调整采样间隔为100ms
        else:
            # 如果不测量偏航角，重置 yaw_list 并重新校准初始 yaw
            yaw_list.clear()
            accel_data = sensor.get_accel_data()
            gyro_data = sensor.get_gyro_data()
            rotation = MPU6050filter.IMUupdate(accel_data['x'], accel_data['y'], accel_data['z'],
                                               gyro_data['x'], gyro_data['y'], gyro_data['z'])
            _, _, initial_yaw = rotation
            time.sleep(0.1)  # 避免频繁校准，增加稳定性

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

def test(status):
    global measure_yaw
    status = int(status)
    
    if status == 0:
        print("停止")
        setGroupRun(0, 1)
        measure_yaw = False
        
    elif status == 1:
        print("前进")
        measure_yaw = True
        
        # 从队列获取最新的yaw平均值
        if not myQueue.empty():
            avg_yaw = myQueue.get()
            print(f"Average Yaw: {avg_yaw}")

            # 判断 yaw 并执行动作
            if avg_yaw > 10:
                setGroupRun(6, 1)
            elif avg_yaw < -10:
                setGroupRun(7, 1)
            else:
                setGroupRun(8, 1)
                
    elif status in [2, 3, 4, 5, 6, 7, 8, 9]:
        print(f"处理状态: {status}")
        measure_yaw = False
        # 执行相应动作组
        group_map = {
            2: 2,  # 前右
            3: 2,  # 右转
            4: 2,  # 右后
            5: 3,  # 后退
            6: 3,  # 左后
            7: 4,  # 左转
            8: 4,   # 前左
            9: 20
            
        }
        setGroupRun(group_map[status], 1)

def main():
    # 创建并启动MPU6050线程
    t1 = threading.Thread(target=t_mpu6050)
    t1.start()

    # 通过回调函数将接收到的status传递给test函数
    receive_data_from_esp32(test)

    t1.join()

if __name__ == '__main__':
    main()
