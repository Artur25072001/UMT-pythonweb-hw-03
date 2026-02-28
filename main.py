import json
import mimetypes
import pathlib
import urllib.parse
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("."))


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)

        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == "/message":
            self.send_html_file("message.html")
        elif pr_url.path == "/read":
            self.render_read_page()
        else:
            file_path = pathlib.Path(pr_url.path[1:])
            if file_path.exists() and not file_path.is_dir():
                self.send_static(file_path)
            else:
                self.send_html_file("error.html", status=404)

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        data = self.rfile.read(content_length)
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {
            key: value for key, value in [el.split("=") for el in data_parse.split("&")]
        }
        self.save_to_json(data_dict)
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def save_to_json(self, new_data):
        file_path = pathlib.Path("storage/data.json")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        content = {}
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    content = json.load(f)
                except json.JSONDecodeError:
                    content = {}
        content[str(datetime.now())] = new_data
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)

    def render_read_page(self):
        file_path = pathlib.Path("storage/data.json")
        messages = {}

        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    messages = json.load(f)
                except json.JSONDecodeError:
                    messages = {}

        template = env.get_template("read.html")
        output = template.render(messages=messages)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(output.encode())

    def send_html_file(self, filename, status=200):
        try:
            with open(filename, "rb") as fd:
                self.send_response(status)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(fd.read())
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"File not found")

    def send_static(self, file_path):
        self.send_response(200)
        mt = mimetypes.guess_type(file_path)
        self.send_header("Content-type", mt[0] if mt[0] else "application/octet-stream")
        self.end_headers()
        with open(file_path, "rb") as file:
            self.wfile.write(file.read())


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    print("Сервер запущено на http://localhost:3000")
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == "__main__":
    run()
