from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import urllib.parse
import mimetypes
import json
from datetime import datetime
import socket
import threading


HTTP_PORT = 3000
SOCKET_PORT = 5000


class MyHTTPRequestHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        
        mime_type, _ = mimetypes.guess_type(path)

        if mime_type is None:
            mime_type = 'text/html'

        if path == '/':
            path = '/index.html'

        try:
            with open(Path('.' + path), 'rb') as file:
                self.send_response(200)
                self.send_header('Content-type', mime_type)
                self.end_headers()
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.send_error(404, 'Not Found')

    def do_POST(self):
        if self.path == '/message':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            parsed_data = urllib.parse.parse_qs(post_data)

            username = parsed_data['username'][0]
            message = parsed_data['message'][0]

            
            send_to_socket_server(username, message)

            
            self.send_response(303)
            self.send_header('Location', '/message.html')
            self.end_headers()
        else:
            self.send_error(404, 'Not Found')



def send_to_socket_server(username, message):
    now = datetime.now()
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S.%f')

    data = {
        timestamp: {
            'username': username,
            'message': message
        }
    }

    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(json.dumps(data).encode('utf-8'), ('localhost', SOCKET_PORT))
    except Exception as e:
        print(f"Помилка при відправленні даних на сокет-сервер: {e}")



def run_http_server():
    server_address = ('', HTTP_PORT)
    httpd = HTTPServer(server_address, MyHTTPRequestHandler)
    print(f"HTTP сервер запущений на порту {HTTP_PORT}")
    httpd.serve_forever()



def run_socket_server():
    data_file = 'storage/data.json'

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(('localhost', SOCKET_PORT))
            print(f"Сокет-сервер запущений на порту {SOCKET_PORT}")
            while True:
                data, _ = sock.recvfrom(1024)
                received_data = json.loads(data.decode('utf-8'))

                with open(data_file, 'r') as file:
                    existing_data = json.load(file)

                existing_data.update(received_data)

                with open(data_file, 'w') as file:
                    json.dump(existing_data, file, indent=2)

    except Exception as e:
        print(f"Помилка при роботі сокет-сервера: {e}")


if __name__ == '__main__':
    
    http_thread = threading.Thread(target=run_http_server)
    socket_thread = threading.Thread(target=run_socket_server)

    http_thread.start()
    socket_thread.start()
