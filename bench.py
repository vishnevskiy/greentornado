from eventlet.green import urllib2
from tornado import ioloop
from tornado.httpclient import AsyncHTTPClient
import eventlet
import time
import greentornado

urls = ["http://www.google.com/intl/en_ALL/images/logo.gif",
         "https://wiki.secondlife.com/w/images/secondlife.jpg",
         "http://us.i1.yimg.com/us.yimg.com/i/ww/beta/y3.gif"]

@greentornado.greenify
def eventlet_scrape():
    def fetch(url):
        print '(Tornado /w Eventlet) Fetch ', url
        urllib2.urlopen(url)
        return url

    pool = eventlet.GreenPool()

    for url in pool.imap(fetch, urls):
        print '(Tornado /w Eventlet) Response ', url

    ioloop.IOLoop().instance().stop()

def normal_scrape():
    global count
    count = 0

    def callback(response):
        print '(Tornado) Response ', response.effective_url

        global count
        count -= 1
        if count == 0:
            ioloop.IOLoop().instance().stop()

    client = AsyncHTTPClient()

    for url in urls:
        print '(Tornado) Fetch', url
        count += 1
        client.fetch(url, callback)

if __name__ == '__main__':
    # (Tornado w/ Eventlet) HTTP Client
    st = time.time()
    eventlet_scrape()
    ioloop.IOLoop().instance().start()
    print time.time() - st

    # (Tornado) HTTP Client
    st = time.time()
    ioloop.IOLoop().instance().add_callback(normal_scrape)
    ioloop.IOLoop().instance().start()
    print time.time() - st

