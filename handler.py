import re
import constant
from utils import sender_actions, send_api, user_profile_api, pass_thread_control_api

from utils import context_manager, message_helper, id_manager, graph_mail_api

# Context manager is for storing the intent behind the last message that was sent by the bot
# It helps in gathering data and handling an edge case where user types out an option
# instead of selecting it in quick replies.

def compare_string_ignore_case_punctuation(str1, str2):
    """comapers sting ignoring special characters and case

    Args:
        str1 (String): String to compare
        str2 (String): String to compare

    Returns:
        Bool: Boolean value indicating equality
    """
    fun = lambda s: re.sub(r"[^\w\s]", "", s).casefold()
    return fun(str1) == fun(str2)

def handle_messaging_object(messaging_object):
    if "message" in messaging_object.keys():
        handle_message(messaging_object)
    elif "postback" in messaging_object.keys():
        handle_postback(messaging_object)
    elif "pass_thread_control" in messaging_object.keys():
        handle_thread_control(messaging_object)

def handle_thread_control(messaging_object):
    """Handles passing of thread control of this app.
    If "list all" is given as metadata. It dumps all the
    stored jokes twice

    Args:
        messaging_object {Dictionary} -- Messaging object recieved by webhook
    """
    psid = messaging_object["sender"]["id"]
    handle_payload(psid, constant.payload.PASS_CONTROL_PAYLOAD)

def handle_message(messaging_object):
    """Handle messaging message object

    Arguments:
        messaging_object {Dictionary} -- Messaging object recieved by webhook
    """
    psid = messaging_object["sender"]["id"]
    sender_actions.inform_user_seen(psid)
    message_object = messaging_object["message"]

    print(psid, flush=True)

    # To check if message has payload to handle quick replies
    # and payload is not one to be discarded
    # (This done as I can't send quick reply without payload)
    if "quick_reply" in message_object.keys():
        # extract payload and handle them the same way as postback payloads
        payload_object = message_object["quick_reply"]["payload"]
        handle_payload(psid, payload_object)
    else:
        text = message_object["text"]

        # cancel any work and restart again
        if compare_string_ignore_case_punctuation(text, constant.message.CANCEL):
            handle_payload(psid, constant.payload.CANCEL_PAYLOAD)

        elif compare_string_ignore_case_punctuation(text, constant.message.EXIT):
            handle_payload(psid, constant.payload.FAST_EXIT)

        # try to handle message based on context
        else:
            context = context_manager.get_context(psid)
            handle_context(psid, context, text)

def handle_postback(messaging_object):
    """Handle messaging postback object

    Arguments:
        messaging_object {Dictionary} -- Messaging object recieved by webhook
    """
    sender_id = messaging_object["sender"]["id"]
    sender_actions.inform_user_seen(sender_id)
    payload_object = messaging_object["postback"]["payload"]
    handle_payload(sender_id, payload_object)


def handle_context(psid, context, message):
    """Handles a message sent by user depending on the context it was sent in.
    In case the message is an option of a quick reply it's payload is forwarded
    to handle_payload

    Arguments:
        psid {String} -- PSID of user
        context {String} -- context of last message sent by us
        message {String} -- message sent by user
    """

    # compares message to quick reply options depending on context
    # and does the work that should be done
    # as the context is stored if the message doesn't match any option we can ask for another one

    if context == constant.context.GET_STARTED_DECISION_CONTEXT:
        if compare_string_ignore_case_punctuation(message, constant.message.YES):
            handle_payload(psid, constant.payload.HAS_PASS_WORD)
        elif compare_string_ignore_case_punctuation(message, constant.message.NO):
            handle_payload(psid, constant.payload.NEW_USER)
        elif compare_string_ignore_case_punctuation(message, constant.message.EXIT):
            handle_payload(psid, constant.payload.FAST_EXIT)
        else:
            send_api.send_simple_message(psid, constant.message.CAN_NOT_UNDERSTAND)

    elif context == constant.context.CANCEL_CONTEXT:
        if compare_string_ignore_case_punctuation(message, constant.message.START):
            handle_payload(psid, constant.payload.PASS_CONTROL_PAYLOAD)
        else:
            send_api.send_simple_message(psid, constant.message.RECOMMEND_START)

    elif context == constant.context.ASK_PASS_WORD_CONTEXT:
        if id_manager.verify_password(message):
            handle_payload(psid, constant.payload.CHECK_MAIL)
        else:
            handle_payload(psid, constant.payload.PASS_WORD_DOES_NOT_EXISTS)

    elif context == constant.context.ASK_COUNTRY_CONTEXT:

        if any(compare_string_ignore_case_punctuation(message, c)
               for c in constant.country_list.values()):
            # sending placeholder values for demo
            send_api.send_simple_message(psid, constant.message.COUNTRY_MATCHED_HOTLINE.format(message))
            send_api.send_simple_message(psid, constant.message.PLACEHOLDER_NUMBER)

            for mess in constant.message.ASK_SECRET_MESSAGE_TEXT:
                send_api.send_simple_message(psid, mess)

            context_manager.store_context(psid, constant.context.ASK_SECRET_MESSAGE_CONTEXT)

            send_api.send_text_with_quick_reply(
                psid,
                constant.message.ASK_SECRET_MESSAGE_CHOICE,
                dict([(constant.message.YES, constant.payload.NEW_CONVO),
                      (constant.message.NO, constant.payload.CANCEL_PAYLOAD),
                      (constant.message.EXIT, constant.payload.FAST_EXIT)])
            )

        else:
            send_api.send_simple_message(psid, constant.message.NO_COUNTRY_MATCH)

    elif context == constant.context.ASK_SECRET_MESSAGE_CONTEXT:
        if compare_string_ignore_case_punctuation(message, constant.message.YES):
            handle_payload(psid, constant.payload.NEW_CONVO)
        elif compare_string_ignore_case_punctuation(message, constant.message.NO):
            handle_payload(psid, constant.payload.CANCEL_PAYLOAD)
        elif compare_string_ignore_case_punctuation(message, constant.message.EXIT):
            handle_payload(psid, constant.payload.FAST_EXIT)
        else:
            send_api.send_simple_message(psid, constant.message.CAN_NOT_UNDERSTAND)

    elif context == constant.context.PASS_WORD_DOES_NOT_MATCH_CHOICE_CONTEXT:
        if compare_string_ignore_case_punctuation(message, constant.message.RETRY):
            handle_payload(psid, constant.payload.HAS_PASS_WORD)
        elif compare_string_ignore_case_punctuation(message, constant.message.NEW_USER):
            handle_payload(psid, constant.payload.NEW_USER)
        elif compare_string_ignore_case_punctuation(message, constant.message.EXIT):
            handle_payload(psid, constant.payload.FAST_EXIT)
        else:
            send_api.send_simple_message(psid, constant.message.CAN_NOT_UNDERSTAND)

    elif context == constant.context.ASK_EMAIL_CONTEXT:
        message_helper.store_email(psid, message)

        context_manager.store_context(psid, constant.context.ASK_FIRST_MESSAGE_CONTEXT)
        message_helper.clear_message(psid)

        for mess in constant.message.ASK_MESSAGE:
            send_api.send_simple_message(psid, mess)

    elif context == constant.context.ASK_FIRST_MESSAGE_CONTEXT:
        if compare_string_ignore_case_punctuation(message, constant.message.DONE):

            password = id_manager.generate_user_id(psid, user_profile_api.get_user_first_name(psid))

            graph_mail_api.send_first_mail(
                id_manager.get_contact_id(psid),
                message_helper.get_email(psid),
                message_helper.get_message(psid)
            )

            for mess in constant.message.MAIL_SENT:
                send_api.send_simple_message(psid, mess)

            context_manager.store_context(psid, constant.context.OPTIONS_CONTEXT)

            send_api.send_simple_message(psid, constant.message.YOUR_PASSWORD.format(password))

            send_api.send_text_with_quick_reply(
                psid,
                constant.message.MAIL_SENT_CHOICE,
                dict([
                    (constant.message.HIDE, constant.payload.FAST_EXIT),
                    (constant.message.CHECK_MAIL, constant.payload.CHECK_MAIL),
                    (constant.message.SEND_MAIL, constant.payload.SEND_MAIL)
                ])
            )

        else:
            message_helper.store_message(psid, message)

    elif context == constant.context.ASK_NEW_MESSAGE_CONTEXT:
        if compare_string_ignore_case_punctuation(message, constant.message.DONE):

            sender_actions.inform_user_typing_on(psid)

            graph_mail_api.send_reply_mail(
                id_manager.get_contact_id(psid),
                message_helper.get_message(psid)
            )

            for mess in constant.message.MAIL_SENT:
                send_api.send_simple_message(psid, mess)

            context_manager.store_context(psid, constant.context.OPTIONS_CONTEXT)

            send_api.send_text_with_quick_reply(
                psid,
                constant.message.MAIL_SENT_CHOICE,
                dict([
                    (constant.message.HIDE, constant.payload.FAST_EXIT),
                    (constant.message.CHECK_MAIL, constant.payload.CHECK_MAIL),
                    (constant.message.SEND_MAIL, constant.payload.SEND_MAIL)
                ])
            )

        else:
            message_helper.store_message(psid, message)

    elif context == constant.context.OPTIONS_CONTEXT:
        if compare_string_ignore_case_punctuation(message, constant.message.HIDE):
            handle_payload(psid, constant.payload.FAST_EXIT)
        elif compare_string_ignore_case_punctuation(message, constant.message.CHECK_MAIL):
            handle_payload(psid, constant.payload.CHECK_MAIL)
        elif compare_string_ignore_case_punctuation(psid, constant.message.SEND_MAIL):
            handle_payload(psid, constant.payload.SEND_MAIL)
        else:
            send_api.send_simple_message(psid, constant.message.CAN_NOT_UNDERSTAND)

    else:
        send_api.send_simple_message(psid, constant.message.CAN_NOT_UNDERSTAND)


def handle_payload(psid, payload):
    """Method to handle payloads recieved

    Arguments:
        psid {String} -- PSID of user
        payload {String} -- payload recieved
    """

    # payload is from get started button. It is the first conversation.
    # Introducing bot and showing options
    if payload == constant.payload.GET_STARTED_PAYLOAD:
        pass_thread_control_api.pass_thread_control(psid, "in between")

    elif payload == constant.payload.PASS_CONTROL_PAYLOAD:

        for mess in constant.message.FIRST_MESSAGE:
            send_api.send_simple_message(
                psid,
                mess
            )

        context_manager.store_context(psid, constant.context.GET_STARTED_DECISION_CONTEXT)

        send_api.send_text_with_quick_reply(
            psid,
            constant.message.FIRST_CHOICE_TEXT,
            dict([(constant.message.YES, constant.payload.HAS_PASS_WORD),
                  (constant.message.NO, constant.payload.NEW_USER),
                  (constant.message.EXIT, constant.payload.FAST_EXIT)]))

    elif payload == constant.payload.HAS_PASS_WORD:

        context_manager.store_context(psid, constant.context.ASK_PASS_WORD_CONTEXT)

        send_api.send_simple_message(
            psid,
            constant.message.ASK_PASS_WORD
        )

    elif payload == constant.payload.NEW_CONVO:
        context_manager.store_context(psid, constant.context.ASK_EMAIL_CONTEXT)
        for mess in constant.message.IN_TEST_MODE:
            send_api.send_simple_message(psid, mess)

    elif payload == constant.payload.PASS_WORD_DOES_NOT_EXISTS:

        context_manager.store_context(psid, constant.context.PASS_WORD_DOES_NOT_MATCH_CHOICE_CONTEXT)

        send_api.send_simple_message(psid, constant.message.PASS_WORD_DOES_NOT_MATCH)

        send_api.send_text_with_quick_reply(
            psid,
            constant.message.PASS_WORD_DOES_NOT_MATCH_CHOICE,
            dict([
                (constant.message.RETRY, constant.payload.HAS_PASS_WORD),
                (constant.message.NEW_USER, constant.payload.NEW_USER),
                (constant.message.EXIT, constant.payload.FAST_EXIT)
            ])
        )

    elif payload == constant.payload.NEW_USER:

        context_manager.store_context(psid, constant.context.ASK_COUNTRY_CONTEXT)

        for s in constant.message.NEW_USER_INTRO:
            send_api.send_simple_message(psid, s)

    elif payload == constant.payload.CHECK_MAIL:
        send_api.send_simple_message(psid, constant.message.MAIL_THREAD)
        sender_actions.inform_user_typing_on(psid)
        cc_id = id_manager.get_contact_id(psid)
        text_messages = graph_mail_api.get_mail_thread(cc_id)
        send_api.send_simple_message(psid, "\n".join(text_messages))

        context_manager.store_context(psid, constant.context.OPTIONS_CONTEXT)

        send_api.send_text_with_quick_reply(
            psid,
            constant.message.MAIL_SENT_CHOICE,
            dict([
                (constant.message.HIDE, constant.payload.FAST_EXIT),
                (constant.message.CHECK_MAIL, constant.payload.CHECK_MAIL),
                (constant.message.SEND_MAIL, constant.payload.SEND_MAIL)
            ])
        )


    elif payload == constant.payload.SEND_MAIL:
        message_helper.clear_message(psid)
        context_manager.store_context(psid, constant.context.ASK_NEW_MESSAGE_CONTEXT)
        send_api.send_simple_message(psid, constant.message.ASK_MESSAGE_MAIN)

    # payload for chat cancelled
    elif payload == constant.payload.CANCEL_PAYLOAD:
        context_manager.store_context(psid, constant.context.CANCEL_CONTEXT)
        for message in constant.message.CANCEL_SIMPLE_MESSAGES:
            send_api.send_simple_message(psid, message)

    # giving control back to main app
    elif payload == constant.payload.FAST_EXIT:
        pass_thread_control_api.pass_thread_control(psid, "list all")