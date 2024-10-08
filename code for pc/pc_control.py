import tkinter
import tkinter.messagebox
import cv2
import socket
import numpy as np
import time
import threading
from tkinter import ttk, Label
from PIL import Image, ImageTk


# 服务函数
def send_code(code):
    def connect():
        HOST = '192.168.137.125'  # 服务器的公网IP
        PORT = 1177
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.connect((HOST, PORT))
        return sock

    def update(data):
        sock.send("up".encode())
        sock.send(str(data).encode())
        print(sock.recv(100))

    sock = connect()
    update(code)


def ui():
    # UI基本文字
    interaction = tkinter.Tk()
    interaction.title("远程遥控")
    interaction.geometry("650x350")  # 增加窗口宽度以显示视频
    interaction.resizable(False, False)
    notebook = tkinter.ttk.Notebook(interaction, width=430, height=320)
    frameOne = tkinter.Frame()
    global frameTwo
    frameTwo = tkinter.Frame()
    frameThree = tkinter.Frame()
    notebook.add(frameOne, text='控制器')
    notebook.place(x=0, y=0)

    # 控制按钮
    botton1 = tkinter.Button(frameOne, text="↑", height=1, width=3, command=lambda: send_code(1)).place(x=200, y=50)
    botton2 = tkinter.Button(frameOne, text="↓", height=1, width=3, command=lambda: send_code(5)).place(x=200, y=150)
    botton3 = tkinter.Button(frameOne, text="←", height=1, width=3, command=lambda: send_code(8)).place(x=150, y=100)
    botton4 = tkinter.Button(frameOne, text="→", height=1, width=3, command=lambda: send_code(2)).place(x=250, y=100)
    botton5 = tkinter.Button(frameOne, text="🛑", height=1, width=3, command=lambda: send_code(0)).place(x=200, y=100)
    botton10 = tkinter.Button(frameOne, text="爬坡", height=2, width=10, command=lambda: send_code(9)).place(x=175, y=200)
    botton11 = tkinter.Button(frameOne, text="切换", height=2, width=10, command=lambda: send_code("a")).place(x=175,y=250)
    # 视频显示区域
    global video_label
    video_label = Label(interaction)
    video_label.place(x=450, y=0)

    # 帮助菜单栏
    def ar():
        tkinter.messagebox.showinfo('关于作者', '来自2022级英才班第八组成员（徐锐洋，彭琬婷，辛英奇，冯乐怡）')

    def he():
        tkinter.messagebox.showinfo('帮助', '遥控六足机器人运动+实时视频显示')

    menubar = tkinter.Menu(interaction)
    helpmenu = tkinter.Menu(menubar, tearoff=0)
    menubar.add_cascade(label='帮助', menu=helpmenu)
    helpmenu.add_command(label='关于', command=lambda: ar())
    helpmenu.add_command(label='说明', command=lambda: he())
    interaction.config(menu=menubar)

    # 开始主循环
    interaction.mainloop()


class myThread(threading.Thread):
    def __init__(self, threadID, name, function):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.function = function

    def run(self):
        self.function()


def t1_go():
    thread1 = myThread(1, "Thread-1", ui)
    thread1.start()


# 实时视频传输类
class ReceiveImg(object):
    def __init__(self, host, port):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))
        self.connection = self.client_socket.makefile('rb')
        self.stream_bytes = b' '

    def read(self):
        try:
            msg = self.connection.read(2048)
            self.stream_bytes += msg
            first = self.stream_bytes.find(b'\xff\xd8')
            last = self.stream_bytes.find(b'\xff\xd9')

            if first != -1 and last != -1:
                jpg = self.stream_bytes[first:last + 2]
                self.stream_bytes = self.stream_bytes[last + 2:]
                image = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                return image

        except:
            print("Error：连接出错！")
            return None


def update_video():
    receiver = ReceiveImg('192.168.137.116', 8000)
    while True:
        img = receiver.read()
        if img is not None:
            img = cv2.resize(img, (320, 240))  # 调整图像大小，降低分辨率
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img)
            img_tk = ImageTk.PhotoImage(image=img_pil)
            video_label.config(image=img_tk)
            video_label.image = img_tk
        #time.sleep(0.005)  # 降低帧率到每秒10帧



# 主函数
if __name__ == '__main__':
    # 启动UI线程
    t1_go()
    # 启动视频更新线程
    thread2 = myThread(2, "Thread-2", update_video)
    thread2.start()
