from http.server import HTTPServer, BaseHTTPRequestHandler


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"<h1>Elders Guild Dashboard</h1><p>WSL2 Connection: OK</p>")


HTTPServer(("0.0.0.0", 8080), H).serve_forever()
