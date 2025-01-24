"""LINE Bot server implementation for stock analysis.

This module implements a Flask server that handles LINE Bot webhook events,
processes user messages using Claude AI, and sends responses back to users
through the LINE Messaging API.
"""

import asyncio
import os

from dotenv import load_dotenv
from flask import Flask, abort, request
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from agents.trial_agent import chat_with_claude
from src.logger import logger

load_dotenv()

app = Flask(__name__)
configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# Create event loop to run async functions
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


@app.route("/callback", methods=["POST"])
def callback():
    """Handle LINE webhook callback.

    Validates the signature and processes the webhook event.

    Returns:
        str: 'OK' if successful

    Raises:
        HTTPException: 400 if signature is invalid
    """
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    """Handle text messages from LINE users.

    Processes the message using Claude AI and sends the response
    back through LINE Messaging API.

    Args:
        event: LINE message event containing the text message
    """
    user_id = event.source.user_id
    text = event.message.text.strip()
    logger.info(f"{user_id}: {text}")

    try:
        # Run async function in the existing event loop
        response = loop.run_until_complete(chat_with_claude(text))

        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token, messages=[TextMessage(text=response)]
                )
            )
    except Exception as e:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token, messages=[TextMessage(text=str(e))]
                )
            )


@app.route("/", methods=["GET"])
def home():
    """Handle requests to the root endpoint.

    Returns:
        str: A simple greeting message
    """
    return "Hello World"


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=8080)
    finally:
        loop.close()
