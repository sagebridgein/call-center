#!/usr/bin/env python3

import http.server
import socketserver
import urllib.parse
import json
import sys

class AJAMHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the URL and query parameters
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        # Only handle AJAM requests (/rawman)
        if not parsed_url.path.startswith('/rawman'):
            # Forward non-AJAM requests to the actual Asterisk ARI
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
            return
        
        # Handle different AJAM actions
        action = query_params.get('action', [''])[0]
        
        if action == 'ping':
            response = {
                'Response': 'Success',
                'Message': 'Pong',
                'Ping': 'Pong',
                'Timestamp': '1755185418.728827'
            }
        elif action == 'login':
            response = {
                'Response': 'Success',
                'Message': 'Authentication accepted'
            }
        elif action == 'logoff':
            response = {
                'Response': 'Success',
                'Message': 'Logged off'
            }
        else:
            response = {
                'Response': 'Error',
                'Message': 'Unknown action'
            }
        
        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        
        # Format response as Asterisk Manager Interface format
        response_text = '\n'.join([f'{k}: {v}' for k, v in response.items()]) + '\n\n'
        self.wfile.write(response_text.encode())
    
    def log_message(self, format, *args):
        # Suppress logging
        pass

if __name__ == '__main__':
    PORTS = [5040, 5041, 5042, 5043, 5044]  # Try multiple ports
    
    for PORT in PORTS:
        try:
            httpd = socketserver.TCPServer(("", PORT), AJAMHandler)
            print(f"AJAM server running on port {PORT}")
            httpd.serve_forever()
            break
        except OSError as e:
            if e.errno == 98:  # Address already in use
                print(f"Port {PORT} is already in use, trying next port...")
                continue
            raise
