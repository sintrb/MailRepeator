#!/usr/bin/env python
# -*- coding: UTF-8 -*
'''
@author: sintrb
'''
"""A simple SMTP Server.

This module refer to SinMail(https://github.com/sintrb/SinMail)

"""

__version__ = "0.0.0"


import smtpd
import asyncore
import os, re, sys
import smtplib
import email.utils
import time, json

options = {
          'proxy':{
            'type':'smtp',
            'server' : 'smtp.163.com',
            'port' : 25,
            'username' : 'xxx@163.com',
            'password' : 'xxx',
            'starttls' : True,
            },
          'realm':'MailRepeator',
          'receivers':['trbbadboy@qq.com', ],
          'bind':'0.0.0.0',
          'port': 25,
          'filter': None,  # ex: '.*@hz.inruan.com'
          'debug':False
        }

def mergedict(dst, src, ignores=None):
    for k, v in src.items():
        if not ignores or k not in ignores:
            if type(v) == dict:
                if k not in dst:
                    dst[k] = {}
                mergedict(dst[k], src[k], ignores)
            else:
                dst[k] = src[k]

def loadconfig():
    global options
    configfile = options.get('configfile')
    if not configfile or not os.path.exists(configfile):
        return False
    if os.stat(configfile).st_mtime == options.get('lastload', 0):
        return  False
    if options.get('debug'):
        print 'load config from: %s' % configfile
    mergedict(options, json.load(open(configfile)))
    options['lastload'] = os.stat(configfile).st_mtime

def config(argv):
    import getopt
    global options
    opts, args = getopt.getopt(argv, "c:r:R:f:t:hd", ["smtp_server=", "smtp_port=", "smtp_username=", "smtp_password=", "smtp_starttls", ])
    for opt, arg in opts:
        if opt == '-r':
            options['realm'] = arg
        if opt == '-c':
            options['configfile'] = os.path.join(os.getcwd(), arg)
        if opt == '-R':
            options['receivers'] = [s.strip() for s in arg.split(';') if s.strip()]
        elif opt == '-d':
            options['debug'] = True
        if opt == '-f':
            options['fromfilter'] = arg
        if opt == '-t':
            options['tofilter'] = arg
        elif opt == '-h':
            print 'Usage: python -m MailRepeator [-c configfile] [-r realm] [-debug] [-R receivers(use ; to split mails)] [-f from-filter] [-t to-filter] [smtp_server=smtp server] [smtp_port=smtp port] [smtp_username=smtp username] [smtp_password=smtp password] [smtp_starttls=smtp starttls] [bindaddress:port | port]'
            print 'Report bugs to <sintrb@gmail.com>'
            exit()
        elif opt.startswith('--smtp_'):
            stmp_opt = opt[7:]
            if stmp_opt == 'port':
                options['proxy'][stmp_opt] = int(arg)
            elif stmp_opt == 'starttls':
                options['proxy'][stmp_opt] = True
            else:
                options['proxy'][stmp_opt] = arg

    if len(args) > 0:
        bp = args[0]
        if ':' in bp:
            options['bind'] = bp[0:bp.index(':')]
            options['port'] = int(bp[bp.index(':') + 1:])
        else:
            options['bind'] = '0.0.0.0'
            options['port'] = int(bp)
    
    loadconfig()

class MainSMTPServer(smtpd.SMTPServer):
    __version__ = 'MainSMTPServer %s' % __version__
    @property
    def options(self):
        global options
        loadconfig()
        return options
    
    def repeatmail(self, mail):
        options = self.options
        proxy = options.get('proxy')
        server = smtplib.SMTP(proxy.get('server'), proxy.get('port', 25))
        server.set_debuglevel(options.get('debug'))  # show communication with the server
        if proxy.get('starttls', False):
            server.ehlo()
            server.starttls()
            server.ehlo()

        if proxy.get('username') and proxy.get('password'):
            server.login(proxy.get('username'), proxy.get('password'))
        
        receivers = options.get('receivers')
        for toaddr in receivers:
            fromaddr = proxy.get('fromaddr') or proxy.get('username')
            del mail['To']
            del mail['From']
            mail['To'] = email.utils.formataddr((re.findall('(\S+)@', toaddr)[0], toaddr))
            mail['From'] = email.utils.formataddr((options.get('realm', self.__version__), fromaddr))
            data = mail.as_string()
            if self.options.get('debug'):
                print '\n--------------S------------------\n', data, '\n---------------------------\n'
            try:
                server.sendmail(fromaddr, [toaddr], data)
            except Exception, e:
                print e
        server.quit()
    
    def process_message(self, peer, mailfrom, rcpttos, data):
        if options.get('fromfilter'):
            if not re.match(options.get('fromfilter'), mailfrom):
                if options.get('debug'):
                    print 'not match from-filter: %s' % mailfrom
                return
        if options.get('tofilter'):
            for tomail in rcpttos:
                if not re.match(options.get('tofilter'), tomail):
                    if options.get('debug'):
                        print 'not match to-filter: %s' % tomail
                    return
        if self.options.get('debug'):
            print '\n-------------R-------------------\n', data, '\n---------------------------\n'
#         self.repeatmail(email.message_from_string(data))
        return
    
    

def start():
    global options
    if options.get('debug'):
        import json
        print json.dumps(options, indent=True)
    addr = (options.get('bind'), options.get('port'))
    smtp_server = MainSMTPServer(addr, None)
    print 'SMTP server @ %s:%s' % addr
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        smtp_server.close()


def main():
    config(sys.argv[1:])
    start()
    
if __name__ == '__main__':
    main()



