import os
from collections import deque
from O365 import Account

cred = (os.getenv("APP_ID"), os.getenv("SECRET"))

account = Account(cred)

# To generate auth tokens and refresh tokens
# app id and secret of the microsoft app
# with Mail.ReadWrite and Mail.Send scopes

if not account.is_authenticated:
    account.authenticate(scopes=['basic', 'message_all'])

def send_first_mail(user_id, email, message):
    """To send a message at the given email for the given user_id

    Args:
        user_id (String): user id to include in email header
        email (String): email id to send the message to
        message (String): message to send
    """

    message = message.replace("\n", "<br>")
    new_message = account.new_message()
    new_message.to.add(email)
    new_message.subject = f"[{user_id}] Help Requested for domestic violence victim"
    new_message.body = f"""
    <html>
        <body>
            <p>
            {message}
            </p>
            <div class ="ashafooter">
            <hr>
            I am contacting you on behalf of a potential domestic violence victim.
            The message above is sent by them. If you send any reply it would be shown to them.
            </div>
        </body>
    </html>
    """
    new_message.send()
    print("Sent")

def send_reply_mail(user_id, message):
    """To send a message as a reply in the conversation thread for the given user_id

    Args:
        user_id (String): user id to include in email header
        message (String): message to send
    """

    message = message.replace("\n", "<br>")
    mails = fetch_mail(user_id)
    que = deque(mails, maxlen=1)
    last_mail = que.pop()
    reply_mail = last_mail.reply()
    reply_mail.body = f"""
    <html>
        <body>
            <p>
            <div class ="usermessage">
            {message}
            </div>
            </p>
            <div class ="ashafooter">
            <hr>
            I am contacting you on behalf of a potential domestic violence victim.
            The message above is sent by them. If you send any reply it would be shown to them.
            </div>
        </body>
    </html>
    """
    reply_mail.send()
    print("Sent")


def get_mail_thread(user_id):
    text_messages = []
    messages = fetch_mail(user_id)
    for message in messages:
        bs = message.get_body_soup()
        text_messages.append("You:" if "ashafbmess@outlook.com" not in message.to else "NGO:")
        for div in bs.select("div[class*=quote], div[class=ashafooter], div[id=divRplyFwdMsg], div:last-child"):
            div.decompose()
        text_messages.append(bs.body.text)
        text_messages.append("\u2501")
    return text_messages
        
def fetch_mail(user_id):
    """Fetch all mails from mailbox for a given user id

    Args:
        user_id (String): Unique Id of user in Header

    Returns:
        List: All messages/mail in thread
    """
    mailbox = account.mailbox()
    query = mailbox.new_query().on_attribute("subject").contains(str(user_id))
    messages = mailbox.get_messages(query=query)
    return messages
