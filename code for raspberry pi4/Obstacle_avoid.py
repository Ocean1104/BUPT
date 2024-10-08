import RPi.GPIO as GPIO
import time
import socket
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
# HC-SR04引脚定义
TRIG = 4
ECHO = 17
INTERVAL = 3

# 舵机引脚定义
SERVO_PIN = 20

# 初始化舵机角度为90度
INITIAL_ANGLE = 75
LEFT_ANGLE = 130
RIGHT_ANGLE = 20

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

# 初始化距离测量
def distanceInit():
    print('Distance Measurement In Progress')
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)

# 单次测距函数
def distanceStart():
    # 发送trig信号，持续10us的方波脉冲
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    # 等待低电平结束，然后记录时间
    while GPIO.input(ECHO) == 0:
        pass
    pulse_start = time.time()

    # 等待高电平结束，然后记录时间
    while GPIO.input(ECHO) == 1:
        pass
    pulse_end = time.time()

    # 计算距离(单位:cm)
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    distance = round(distance, 2)
    return distance

# 计算6次测距的平均值
def getAverageDistance(samples=6):
    distances = []
    for _ in range(samples):
        distance = distanceStart()
        distances.append(distance)
        time.sleep(0.1)  # 适当的延迟，避免过于频繁的测量
    avg_distance = sum(distances) / len(distances)
    return round(avg_distance, 2)

# 角度转为占空比
def angleToDutyCycle(angle):
    return 2.5 + angle / 180.0 * 10

# 舵机初始化
def servoInit():
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    p = GPIO.PWM(SERVO_PIN, 50)  # 初始频率为50Hz
    p.start(angleToDutyCycle(INITIAL_ANGLE))  # 舵机初始化角度为90度
    time.sleep(0.5)
    p.ChangeDutyCycle(0)  # 清空当前占空比，使舵机停止抖动
    return p

# 旋转舵机并测距
def rotateAndMeasure(p, angle):
    print(f'旋转到{angle}度测距...')
    p.ChangeDutyCycle(angleToDutyCycle(angle))
    time.sleep(0.5)
    p.ChangeDutyCycle(0)  # 清空当前占空比，使舵机停止抖动
    time.sleep(0.5)  # 等待舵机稳定后再测距
    distance = distanceStart()  # 单次测距
    print(f"距离: {distance}cm")
    return distance
# 回到初始角度
def rotateToInitial(p):
    p.ChangeDutyCycle(angleToDutyCycle(INITIAL_ANGLE))
    time.sleep(0.5)
    p.ChangeDutyCycle(0)  # 清空当前占空比，使舵机停止抖动
    time.sleep(0.5)  # 等待舵机稳定

# 主程序
try:
    distanceInit()
    servo = servoInit()
    setGroupRun(0, 1)
    while True:
        distance = distanceStart()  # 单次测距
        
        while distance > 30:
            # 当距离大于30cm时，运行动作组1
            distance = getAverageDistance()  # 获取6次测距的平均值
            setGroupRun(1, 1)
            print(f"平均距离: {distance}cm")
        
        # 当距离小于等于30cm时，停止动作组并测量左、右两侧
        print("距离小于等于30cm")
        setGroupRun(0, 1)
        left_distance = rotateAndMeasure(servo, LEFT_ANGLE)
        right_distance = rotateAndMeasure(servo, RIGHT_ANGLE)
        # 回到初始角度，不打印距离
        rotateToInitial(servo)

        if left_distance > 30:
                print("向左转")
                setGroupRun(4, 1)
                break
        if right_distance > 30
                print("向右转")
                setGroupRun(2, 1)  
        else:
            print("向右转")
            i=0
            if i in range(6):
                setGroupRun(2, 1)
            
            
               
        time.sleep(INTERVAL)

except KeyboardInterrupt:
    if servo != None:
        servo.stop()
    GPIO.cleanup()
