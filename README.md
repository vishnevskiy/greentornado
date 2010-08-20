Allows Eventlet to run on top of Tornado's IOLoop.

Web Crawler
===========

    from eventlet.green import urllib2
    from tornado import ioloop
    import eventlet
    import greentornado

    def scrape():
        urls = ["http://www.google.com/intl/en_ALL/images/logo.gif",
             "https://wiki.secondlife.com/w/images/secondlife.jpg",
             "http://us.i1.yimg.com/us.yimg.com/i/ww/beta/y3.gif"]

        def fetch(url):
            print 'Fetching'
            return urllib2.urlopen(url).read()

        pool = eventlet.GreenPool()

        for body in pool.imap(fetch, urls):
            print 'Got Body', len(body)

        ioloop.IOLoop().instance().stop()

    if __name__ == '__main__':
        greentornado.join_ioloop(scrape)
        ioloop.IOLoop().instance().start()

HTTP Proxy
==========

from eventlet.green import urllib2
from tornado import httpserver, ioloop
import greentornado

@greentornado.greenify
def handle_request(request):
    body = urllib2.urlopen('http://blog.eventlet.net/feed/').read()
    request.write('HTTP/1.1 200 OK\r\nContent-Length: %d\r\n\r\n%s' % (len(body), body))
    request.finish()

if __name__ == '__main__':
    greentornado.join_ioloop()
    httpserver.HTTPServer(handle_request).listen(8888)
    ioloop.IOLoop.instance().start()

web.py
===========

    import tornado.httpserver
    import tornado.ioloop
    import tornado.web
    import greentornado

    @greentornado.greenify
    class MainHandler(tornado.web.RequestHandler):
        def get(self):
            self.write("Hello, world")

    application = tornado.web.Application([
        (r'/', MainHandler),
    ])

    if __name__ == '__main__':
        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(8888)
        greentornado.join_ioloop()
        tornado.ioloop.IOLoop.instance().start()


