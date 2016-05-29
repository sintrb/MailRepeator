import smtplib
import email.utils
from email.mime.text import MIMEText

msg = MIMEText('This is the body of the message.')
msg['To'] = email.utils.formataddr(('Recipient', '4724970284@qq.com'))
msg['From'] = email.utils.formataddr(('Author', 'x@example.com'))
msg['Subject'] = 'Simple test message'
print type(msg)
server = smtplib.SMTP('127.0.0.1', 25)
# server.set_debuglevel(True) # show communication with the server
try:
    server.sendmail('author@example.com', ['4724970284@qq.com'], msg.as_string())
finally:
    server.quit()
    