"""LINE Bot server implementation for stock analysis.

This module implements a Flask server that handles LINE Bot webhook events,
processes user messages using Claude AI, and sends responses back to users
through the LINE Messaging API.
"""

import asyncio
import os
from typing import Dict

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

from agents.trial_agent import Agent
from src.logger import logger
from tools.analysis.analysis_tool import AnalysisTool
from tools.research.research_tool import ResearchTool
from tools.research.search_framework_tool import SearchFrameworkTool
from tools.time.time_tool import TimeTool

load_dotenv()

app = Flask(__name__)
configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# Create event loop to run async functions
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Dictionary to store agents for each user
agent_management: Dict[str, Agent] = {}


def create_agent() -> Agent:
    """Create a new agent instance with all necessary tools."""
    agent = Agent(
        provider="anthropic",
        model_name="claude-3-sonnet-20240229",
        tools={},  # Empty tools dict initially
    )

    # Set up tools using the created agent
    tools = {
        "research": ResearchTool(lambda news: agent.company_news.extend(news)),
        "time_tool": TimeTool(),
        "search_framework": SearchFrameworkTool(),
        "analysis_report": AnalysisTool(lambda: agent.company_news),
    }

    # Update agent's tools
    agent.tools = tools
    return agent


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
        # Create new agent for user if not exists
        if user_id not in agent_management:
            agent_management[user_id] = create_agent()

        # Get user's agent and process message
        user_agent = agent_management[user_id]
        response = loop.run_until_complete(user_agent.chat(text))
        msg = TextMessage(text=response)

        # Send response
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(reply_token=event.reply_token, messages=[msg])
            )

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            error_message = "處理訊息時發生錯誤，請稍後再試"
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=error_message)],
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
        app.run(host="0.0.0.0", port=8888)
    finally:
        loop.close()
