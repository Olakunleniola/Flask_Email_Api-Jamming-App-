#! /usr/bin/env python3

import email.message
import mimetypes
import os.path
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def generate_with_attachment(sender, recipient, subject, body, attachment_path):
  """Creates an email with an attachement."""
  # Basic Email formatting
  message = email.message.EmailMessage()
  message["From"] = sender
  message["To"] = recipient
  message["Subject"] = subject
  message.set_content(body)
  # Process the attachment and add it to the email
  attachment_filename = os.path.basename(attachment_path)
  mime_type, _ = mimetypes.guess_type(attachment_path)
  mime_type, mime_subtype = mime_type.split('/', 1)

  with open(attachment_path, 'rb') as ap:
    message.add_attachment(ap.read(),
                          maintype=mime_type,
                          subtype=mime_subtype,
                          filename=attachment_filename)

  return message

def generate_no_attachment(sender,recipient,subject,body):
  """Creates an email with an attachement."""
  # Basic Email formatting
  message = email.message.EmailMessage()
  message["From"] = sender
  message["To"] = recipient
  message["Subject"] = subject
  message.set_content(body)

  return message

def send(message,sender, password):
  """Sends the message to the configured SMTP server."""
  mail_server = smtplib.SMTP_SSL('smtp.gmail.com')
  mail_server.login(sender,password)
  mail_server.send_message(message)
  mail_server.quit()

def send_html_mail(sender, recipient, subject, body, password):
  message = MIMEMultipart('alternative')
  message["From"] = sender
  message["To"] = recipient
  message["Subject"] = subject
  msg = MIMEText(body, 'html')
  message.attach(msg)
  mail_server = smtplib.SMTP_SSL('smtp.gmail.com')
  mail_server.login(sender,password)
  mail_server.sendmail(sender, recipient, message.as_string())
  mail_server.quit()
  
  