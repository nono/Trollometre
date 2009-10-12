#!/usr/bin/env python
import daemon
import lxml.html
import math
import os.path
import sys
import string
import pickle
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
			debug=True,
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
        self.doc = lxml.html.fromstring(body.decode('utf8'))

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
        #txt = '<div style="position:fixed;top:0px;left:0px;background-color:green;width=100%%;height=4px"><span style="background-color:red;width=(%.1f)%%;" >trollscore&nbsp;"</span></div>' % score * 10 
        #if score > 10.0:
        #    txt = '/!\\ ' + txt
        trolldiv = lxml.html.Element('span')
        trolldivmetre = lxml.html.Element('span')
        trolldiv.attrib['style'] = 'line-height:8px:max-height:8px;font-family:arial;display:block;position:fixed;top:0px;left:0px;background-color:green;width:100% !important;height:8px'
        trolldivmetre = lxml.html.Element('span')
        trolldivmetre.attrib['style'] ='display:block;background-color:red;width:%.1f%%;font-size:8px;line-height:8px' % int(score * 10)
        trolldivmetre.text='Trollometer'
        trolldivreturn = lxml.html.Element('a')
        trolldivreturn.attrib['onlClick']= "history.go(-1)"
        trolldivreturn.attrib['href']= "#"
        trolldivreturn.attrib['style'] ='display:inline;color:white;background-color:blue;float:right;font-size:8px;line-height:8px;width:20px;padding-left:-20px'
        trolldivreturn.text='back...'
        trolldiv.append(trolldivmetre)
        trolldiv.append(trolldivreturn)

        self.doc.body.append(trolldiv)

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
    http_server.listen(8000)
    tornado.ioloop.IOLoop.instance().start()

