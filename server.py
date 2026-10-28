#!/usr/bin/env python3
"""Serve TypeRip locally and proxy Adobe Fonts family/collection pages."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != '/adobe-page':
            return super().do_GET()
        url = parse_qs(parsed.query).get('url', [''])[0]
        target = urlparse(url)
        if (target.scheme != 'https' or target.netloc != 'fonts.adobe.com'
                or not (target.path.startswith('/fonts/') or target.path.startswith('/collections/'))):
            self.send_error(400, 'Expected an Adobe Fonts family or collection URL')
            return
        try:
            request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(request, timeout=20) as response:
                final = urlparse(response.url)
                if final.scheme != 'https' or final.netloc != 'fonts.adobe.com':
                    self.send_error(502, 'Unexpected redirect from Adobe Fonts')
                    return
                body = response.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (HTTPError, URLError, TimeoutError) as error:
            self.send_error(502, 'Could not fetch Adobe Fonts: ' + str(error))

if __name__ == '__main__':
    print('TypeRip is available at http://127.0.0.1:8765', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8765), Handler).serve_forever()
