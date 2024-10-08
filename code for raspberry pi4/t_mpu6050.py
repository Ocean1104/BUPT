import socket
import time
import serial
import threading
import queue
from mpu6050 import mpu6050
import MPU6050filter

serialHandle = serial.Serial("/dev/ttyS0", 9600)

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