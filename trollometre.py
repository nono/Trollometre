#!/usr/bin/env python
import daemon
import lxml.html
import math
import os.path
import sys
import string
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
			#debug=True,
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static")
        )
        tornado.web.Application.__init__(self, handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


class Page(object):
    words = frozenset([w.strip() for w in open("liste.txt")])

    def __init__(self, body):
        self.doc = lxml.html.fromstring(body)

    def absolute_links(self, url):
        self.doc.make_links_absolute(url)
        base = lxml.html.Element('base', dict(href=url))
        self.doc.head.append(base)

    def compute_score(self):
        txt = self.doc.text_content()
        for punct in string.punctuation:
            txt = txt.replace(punct," ")
        txt = txt.split()
        count = len(filter(lambda x: x in self.words, txt))
        return count / math.log10(2 + len(txt))

    def inject_score(self, score):
        title = self.doc.head.find('title')
        txt = '(%.1f) ' % score
        if score > 10.0:
            txt = '/!\\ ' + txt
        if title is not None:
            title.text = txt + title.text
        else:
            title = lxml.html.Element('title')
            title.text = txt
            self.doc.head.append(title)

    def tostring(self):
        return lxml.html.tostring(self.doc)


class MeasureHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        url = self.get_argument("url")
        http = tornado.httpclient.AsyncHTTPClient()
        http.fetch(url, callback=self.async_callback(self.on_response, url))

    def on_response(self, url, response):
        if response.error: raise tornado.web.HTTPError(500)
        page = Page(response.body)
        page.absolute_links(url)
        score = page.compute_score()
        page.inject_score(score)
        self.write(page.tostring())
        self.finish()


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
        log = open('tornado.' + str(port) + '.log', 'a+')
        ctx = daemon.DaemonContext(
                stdout=log,
                stderr=log,
                working_directory='.'
        )
        ctx.open()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(port, '127.0.0.1')
    tornado.ioloop.IOLoop.instance().start()

