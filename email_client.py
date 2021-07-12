

import imaplib
import smtplib
import re
import email
from email.mime.text import MIMEText
from email.header import decode_header

import logging
from config import Config
import requests
logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s %(message)s", level=logging.INFO)


class EmailClient(object):
    def __init__(self, config_file, log_level=logging.INFO) :
        self.config = Config(config_file)
        self.username = self.config.get("monitor", "monitor.account") 
        self.server = self.config.get("monitor", "imap.server")
        self.password = self.config.get("monitor", "monitor.password")

        # create an IMAP4 class with SSL 
        self.conn = imaplib.IMAP4_SSL(self.server)
        self.conn.login(self.username, self.password)
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(log_level)
        
    def delete_all_email(self):
        self.conn.select('Inbox')
        typ, data = self.conn.search(None, 'ALL')
        for num in data[0].split():
            self.conn.store(num, '+FLAGS', '\\Deleted')

    def send_email(self, subject, message, receiver):

        msg = MIMEText(message)

        msg['Subject'] = subject
        msg['From'] = self.username
        msg['To'] = receiver
        
        smtp_conn = smtplib.SMTP_SSL(self.server, smtplib.SMTP_SSL_PORT)            
        smtp_conn.login(self.username, self.password)

        self.log.info('{} {} {}'.format(self.username, receiver, msg.as_string()))
        smtp_conn.sendmail(self.username, receiver, msg.as_string())
        self.log.info('Successfully sent email to {}'.format(receiver))
        # close the connection and logout
        smtp_conn.quit()

    def get_email(self, from_sender):
        email = re.search(r'[\w\.-]+@[\w\.-]+', from_sender)
        if email is None:
            return None
        return email.group(0)

    def get_validation_email (self, required_sender, required_subject):

        results = ""
        self.conn.select(readonly=1)

        #Get id of unread messages
        status, messages = self.conn.search(None, '(UNSEEN)')
        #get mail ids as strings
        mail_ids = messages[0].decode()
        #split into a list
        id_list = mail_ids.split()
        int_id_list = [int(item) for item in id_list]

        #loop through all mails
        for i in int_id_list:
            # fetch the email message by ID
            status, msg = self.conn.fetch(str(i), "(RFC822)")
            for response in msg:
                if isinstance(response, tuple):
                    # parse a bytes email into a message object
                    msg = email.message_from_bytes(response[1])
                    # decode the email subject
                    subject, encoding = decode_header(msg["Subject"])[0]

                    if isinstance(subject, bytes):
                        # if it's a bytes, decode to str
                        subject = subject.decode(encoding)
                    # decode email sender
                    sender, encoding = decode_header(msg.get("From"))[0]
                    if isinstance(sender, bytes):
                        sender = sender.decode(encoding)
                        
                    #If From and Subject matches requirement, get the email body
                    sender = self.get_email(sender)
                    if (sender == required_sender) and (subject == required_subject):
                        # if the email message is multipart
                        if msg.is_multipart():
                            # iterate over email parts
                            for part in msg.walk():
                                # extract content type of email
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                try:
                                    # get the email body
                                    body = part.get_payload(decode=True).decode()
                                except:
                                    pass
                                if content_type == "text/html":
                                    # print text/plain emails and skip attachments
                                    results += body
                        else:
                            # extract content type of email
                            content_type = msg.get_content_type()
                            # get the email body
                            body = msg.get_payload(decode=True).decode()
                            if content_type == "text/html":
                                # print only text email parts
                                results += body
                                            
        # # close the connection and logout
        # conn.close()
        # conn.logout()
        return results