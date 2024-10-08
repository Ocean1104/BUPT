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
                        status = data.decode('utf-8')
                        callback(status)  # 使用回调函数将 status 值传递出去

                except (socket.error, Exception) as e:
                    break

        except (socket.error, Exception) as e:
            time.sleep(1)

        finally:
            client_socket.close()