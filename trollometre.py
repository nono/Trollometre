#!/usr/bin/env python
import lxml.html
import os.path
import sys
import tornado.escape
import tornado.httpclient
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
    @tornado.web.asynchronous
    def get(self):
        url = self.get_argument("url")
        http = tornado.httpclient.AsyncHTTPClient()
        http.fetch(url, callback=self.async_callback(self.on_response, url))

    def on_response(self, url, response):
        if response.error: raise tornado.web.HTTPError(500)
        doc = lxml.html.fromstring(response.body.decode('utf8'))
        words = set([w.strip() for w in open("liste.txt")])
        count = str(len([x for x in doc.text_content().split(' ') if x in words]))
        doc.make_links_absolute(url)
        base = lxml.html.Element('base', dict(href=url))
        doc.head.append(base)
        title = doc.head.find('title')
        if title is not None:
            title.text = '(' + count + ') ' + title.text
        else:
            title = lxml.html.Element('title')
            title.text = '(' + count + ')'
            doc.head.append(title)
        body = lxml.html.tostring(doc)
        self.write(body)
        self.finish()


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(port)
    tornado.ioloop.IOLoop.instance().start()
