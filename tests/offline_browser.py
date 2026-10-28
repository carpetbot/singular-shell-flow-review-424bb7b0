"""Fail closed in the server too, including browser route teardown races."""
import http.server
from typing import Any, cast
from urllib.parse import urlsplit

class OfflineServer(http.server.ThreadingHTTPServer):
 unexpected_upstream: list[tuple[str,str]]

def offline_server(handler: Any) -> OfflineServer:
 class OfflineHandler(handler):
  def handle(self):
   # Navigating away can also cancel an ordinary static-file response.
   try:super().handle()
   except (BrokenPipeError,ConnectionResetError):pass
  def _proxy(self,method):
   # Keep only method/path, never request headers, credentials or query data.
   self.server.unexpected_upstream.append((method,urlsplit(self.path).path))
   body=b'{"error":"offline fixture: unhandled gateway request"}'
   try:
    self.send_response(503);self.send_header('Content-Type','application/json')
    self.send_header('Content-Length',str(len(body)));self.end_headers()
    if method!='HEAD':self.wfile.write(body)
   except (BrokenPipeError,ConnectionResetError):pass
  def log_message(self,*args):pass
 server=OfflineServer(('127.0.0.1',0),cast(Any,OfflineHandler))
 server.unexpected_upstream=[]
 return server

def close_browser(browser):
 # Leave each origin with interception still installed, before Chromium removes
 # its routes. This cancels observers/media without forwarding in-flight traffic.
 for context in browser.contexts:
  for page in context.pages:
   if not page.is_closed():page.goto('about:blank')
 browser.close()
