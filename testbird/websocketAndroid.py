# -*- encoding:utf-8 -*-


import tornado.web
import tornado.websocket
import tornado.httpserver
import tornado.ioloop
import socket
import binascii as B


class IndexPageHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        ip_port = ('127.0.0.1', 1717)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(ip_port)
        pass

    def on_message(self, message):
        readBannerBytes = 0
        bannerLength = 2
        readFrameBytes = 0
        frameBodyLength = 0
        frameBody = bytes()
        banner = {
            'version': 0
            , 'length': 0
            , 'pid': 0
            , 'realWidth': 0
            , 'realHeight': 0
            , 'virtualWidth': 0
            , 'virtualHeight': 0
            , 'orientation': 0
            , 'quirks': 0
        }
        while True:
            buf = self.sock.recv(4096)
            print len(buf)
            cursor2 = 0
            cursor = 0
            for value in buf:
                if cursor2 > cursor:
                    cursor += 1
                    continue
                value = int(B.b2a_hex(value), 16)
                if readBannerBytes < bannerLength:
                    if readBannerBytes == 0:
                        # banner.version = chunk[cursor]
                        banner['version'] = value
                    elif readBannerBytes == 1:
                        # banner.length = bannerLength = chunk[cursor]
                        banner['length'] = value
                        bannerLength = value
                    elif readBannerBytes in [2, 3, 4, 5]:
                        # banner.pid +=(chunk[cursor] << ((readBannerBytes - 2) * 8)) >>> 0
                        banner['pid'] += (value << ((readBannerBytes - 2) * 8))
                    elif readBannerBytes in [6, 7, 8, 9]:
                        # banner.realWidth +=(chunk[cursor] << ((readBannerBytes - 6) * 8)) >>> 0
                        banner['realWidth'] += (value << ((readBannerBytes - 6) * 8))
                    elif readBannerBytes in [10, 11, 12, 13]:
                        # banner.realHeight += (chunk[cursor] << ((readBannerBytes - 10) * 8)) >>> 0
                        banner['realHeight'] += (value << ((readBannerBytes - 10) * 8))
                    elif readBannerBytes in [14, 15, 16, 17]:
                        # banner.virtualWidth +=(chunk[cursor] << ((readBannerBytes - 14) * 8)) >>> 0
                        banner['virtualWidth'] += (value << ((readBannerBytes - 14) * 8))
                    elif readBannerBytes in [18, 19, 20, 21]:
                        # banner.virtualHeight +=(chunk[cursor] << ((readBannerBytes - 18) * 8)) >>> 0
                        banner['virtualHeight'] += (value << ((readBannerBytes - 18) * 8))
                    elif readBannerBytes == 22:
                        # banner.orientation += chunk[cursor] * 90
                        banner['orientation'] += value * 90
                    elif readBannerBytes == 23:
                        # banner.quirks = chunk[cursor]
                        banner['orientation'] = value
                    readBannerBytes += 1
                    cursor += 1
                    if readBannerBytes == bannerLength:
                        print 'banner', banner
                elif readFrameBytes < 4:
                    # frameBodyLength += (chunk[cursor] << (readFrameBytes * 8)) >>> 0
                    frameBodyLength += (value << (readFrameBytes * 8))
                    readFrameBytes += 1
                    cursor += 1
                    # console.info('headerbyte%d(val=%d)', readFrameBytes, frameBodyLength)
                    print 'headerbyte%d(val=%d)' % (readFrameBytes, frameBodyLength)
                else:
                    if len(buf) - cursor >= frameBodyLength:
                        frameBody += buf[cursor:cursor + frameBodyLength]
                        # print [B.a2b_hex(i) for i in buf[cursor:cursor+frameBodyLength]]
                        cursor2 = cursor + frameBodyLength
                        frameBodyLength = 0
                        readFrameBytes = 0
                        frameBody2 = frameBody
                        frameBody = bytes()
                        self.write_message(frameBody2, binary=True)
                    else:
                        print 'body(len=%d)' % (len(buf) - cursor)
                        frameBody += buf[cursor:]
                        frameBodyLength -= len(buf) - cursor
                        readFrameBytes += len(buf) - cursor
                        cursor2 = len

    def on_close(self):
        pass


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', IndexPageHandler),
            (r'/ws', WebSocketHandler)
        ]

        settings = {"template_path": "."}
        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == '__main__':
    ws_app = Application()
    server = tornado.httpserver.HTTPServer(ws_app)
    server.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
