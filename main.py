from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from datetime import datetime
import urllib.parse
import pathlib
import mimetypes
import socket
import json




class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        print(data)

        data_parse = urllib.parse.unquote_plus(data.decode())
        print(data_parse)
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        print(data_dict)

        self.send_data_via_socket(data_dict)
        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()            

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())        

    def send_data_via_socket(self, data_dict):
        udp_ip = "127.0.0.1"
        udp_port = 5000

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        message = json.dumps(data_dict).encode('utf-8')
        print(f'send -> {message}')
        sock.sendto(message, (udp_ip, udp_port))

        sock.close()



def server_socket():
    print("socket start listening")
    udp_ip = "127.0.0.1"
    udp_port = 5000

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((udp_ip, udp_port))

    while True:
        data, _ = sock.recvfrom(1024)
        data_dict = json.loads(data.decode('utf-8'))
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        new_data_dict = {timestamp: {'username':data_dict['username'],'message':data_dict['message']}}
        
        try:
            with open('storage/data.json', 'r') as json_file:
                all_messages = json.load(json_file)
        except FileNotFoundError:
            all_messages = {}

        all_messages.update(new_data_dict)

        with open('storage/data.json', 'w') as json_file:
            json.dump(all_messages, json_file, indent=4) 
    

def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        socket_server = Thread(target=server_socket)
        socket_server.start()
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()



if __name__ == '__main__':
    run()

