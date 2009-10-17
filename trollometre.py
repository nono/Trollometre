#!/usr/bin/env python
# -*- coding: utf-8 -*-
import daemon
import lxml.html
import math
import os.path
import re
import sys
import string
import tornado.escape
import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.web


class Application(tornado.web.Application):
    def __init__(self, debug):
        handlers = [
            (r"/", MainHandler),
            (r"/measure", MeasureHandler)
        ]
        settings = dict(
            debug=debug,
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static")
        )
        tornado.web.Application.__init__(self, handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


class Page(object):
    words = frozenset([w.strip() for w in open("liste.txt")])
    divstyle = 'position: fixed; top: 0px; left: 0px; width: 100%; height: 10px; line-height: 8px; font-size: 8px; background-color: #08ac56;'
    divmetrestyle  = 'width: %.1f%%; height: 10px; padding: 0 2px; background-color: #ff180b;'
    divmetretext   = u'Trollomètre'
    divreturnstyle = 'position: fixed; top: 0px; right: 0px; height: 10px; padding: 0 2px; color: white; background-color: #3c657b;'
    divreturntext  = 'back'

    def __init__(self, body):
        try:
            self.doc = lxml.html.fromstring(body.decode('utf8'))
        except ValueError:
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
            score = 10
        if title is not None:
            title.text = txt + title.text
        else:
            title = lxml.html.Element('title')
            title.text = txt
            self.doc.head.append(title)
        div = lxml.html.Element('div')
        div.attrib['style'] = self.divstyle
        divmetre = lxml.html.Element('div')
        divmetre.attrib['style'] = self.divmetrestyle % int(score * 10)
        divmetre.text = self.divmetretext
        divreturn = lxml.html.Element('a')
        divreturn.attrib['onClick'] = "history.go(-1)"
        divreturn.attrib['href'] = "#"
        divreturn.attrib['style'] = self.divreturnstyle
        divreturn.text = self.divreturntext
        div.append(divmetre)
        div.append(divreturn)
        self.doc.body.append(div)

    def tostring(self):
        return lxml.html.tostring(self.doc)


class MeasureHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        url = self.get_argument("url")
        if (not re.search('://', url)):
            url = "http://" + url
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
    debug = True
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
        debug = False
        log = open('tornado.' + str(port) + '.log', 'a+')
        ctx = daemon.DaemonContext(
                stdout=log,
                stderr=log,
                working_directory='.'
        )
        ctx.open()
    http_server = tornado.httpserver.HTTPServer(Application(debug))
    http_server.listen(port, '127.0.0.1')
    tornado.ioloop.IOLoop.instance().start()

