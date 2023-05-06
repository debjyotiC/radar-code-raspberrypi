import threading
import os


def web_server():
    # code for the first thread
    os.system(
        "C:\\Users\\Deb\\anaconda3\\envs\\radar-code\\python.exe C:\\Users\\Deb\\PycharmProjects\\radar-code\\radar_data_web_render.py")


def data_classifier():
    os.system(
        "C:\\Users\\Deb\\anaconda3\\envs\\radar-code\\python.exe C:\\Users\\Deb\\PycharmProjects\\radar-code\\real_time_classifier.py")


thread1 = threading.Thread(target=web_server)
thread2 = threading.Thread(target=data_classifier)

thread1.start()
thread2.start()

thread1.join()
thread2.join()

print("Both threads have finished running")
