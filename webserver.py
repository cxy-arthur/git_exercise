"""
web server 服务程序
"""
from socket import *
from select import select
import re


# 处理客户端请求
class Handle:
    def __init__(self, html=""):
        self.html = html

    # 组织响应
    def send_response(self, connfd, info):
        # info --> /   /abc.html  /xxxx.png
        if info == '/':
            filename = self.html + "/index.html"
        else:
            filename = self.html + info
        # 组织响应
        try:
            file = open(filename, 'rb')
        except:
            # 文件不存在
            response = "HTTP/1.1 404 Not Found\r\n"
            response += "Content-Type:text/html\r\n"
            response += "\r\n"
            with open(self.html + "/404.html") as file:
                response += file.read()
            response = response.encode()
        else:
            # 请求的网页存在
            response = "HTTP/1.1 200 OK\r\n"
            response += "Content-Type:text/html\r\n"
            response += "\r\n"
            response = response.encode() + file.read()
        finally:
            connfd.send(response)

    # 具体处理浏览器http请求
    def manager(self, connfd):
        # 　接收ｈｔｔｐ请求
        request = connfd.recv(1024).decode()
        if not request:
            raise Exception  # 防止客户端异常退出
        # 匹配出请求内容
        pattarn = r"[A-Z]+\s+(?P<info>/\S*)"
        result = re.match(pattarn, request)
        if result:
            info = result.group("info")
            print("请求内容:", info)
            self.send_response(connfd, info)


class WebServer:
    def __init__(self, host="", port=0, html=None):
        self.host = host
        self.port = port
        self.html = html
        self.address = (host, port)
        self.rlist = []
        self.wlist = []
        self.xlist = []
        self.handle = Handle(self.html)  # 实例化处理类对象
        self.sock = self.__create_socket()

    # 准备tcp套接字
    def __create_socket(self):
        sock = socket()
        sock.bind(self.address)
        sock.setblocking(False)
        return sock

    # 处理浏览器连接
    def __connect(self):
        connfd, add = self.sock.accept()
        connfd.setblocking(False)
        self.rlist.append(connfd)

    # 启动服务
    def start(self):
        self.sock.listen(5)
        print("Listen the port %d" % self.port)
        self.rlist.append(self.sock)  # 监控监听套接字
        # IO多路服用模型
        while True:
            rs, ws, xs = select(self.rlist, self.wlist, self.xlist)
            for r in rs:
                print(r)
                if r is self.sock:
                    self.__connect()
                else:
                    try:
                        self.handle.manager(r)
                    except Exception as e:
                        print(e)
                    finally:
                        self.rlist.remove(r)  # 如果不删除套接字,X掉刷新之后初始套接字会持续发空 导致该事件的读套接字一直就绪
                        r.close()  # close之后文件标识符是负数


if __name__ == '__main__':
    # 先确定类的使用方法
    # 什么数据量是用户决定的
    httpd = WebServer(host="0.0.0.0", port=8000, html="./static")
    httpd.start()  # 启动服务
