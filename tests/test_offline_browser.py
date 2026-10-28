"""Offline fixture disconnects are quiet; real handler errors stay visible."""
import unittest
from typing import Any
from offline_browser import offline_server

class OfflineHarness(unittest.TestCase):
 def test_disconnected_static_response_is_quiet_but_real_errors_surface(self):
  for error in [BrokenPipeError,ConnectionResetError,RuntimeError]:
   with self.subTest(error=error.__name__):
    class AbortedStatic:
     def handle(self):raise error('fixture static write')
    server=offline_server(AbortedStatic)
    try:
     cls: Any=server.RequestHandlerClass
     handler=object.__new__(cls)
     if error is RuntimeError:
      with self.assertRaises(RuntimeError):handler.handle()
     else:handler.handle()
     self.assertEqual(server.unexpected_upstream,[])
    finally:server.server_close()

if __name__=='__main__':unittest.main()
