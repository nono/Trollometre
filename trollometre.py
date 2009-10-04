#!/usr/bin/env python
import os.path
import sys
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.web


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/measure", MeasureHandler)
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static")
        )
        tornado.web.Application.__init__(self, handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
  def get(self):
    self.render("index.html")


class MeasureHandler(tornado.web.RequestHandler):
  def get(self):
    url = self.get_argument("url")
    self.write(url)


if __name__ == "__main__":
  port = 8000
  if len(sys.argv) > 1:
    port = int(sys.argv[1])
  http_server = tornado.httpserver.HTTPServer(Application())
  http_server.listen(port)
  tornado.ioloop.IOLoop.instance().start()
