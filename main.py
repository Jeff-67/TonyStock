"""LINE Bot server implementation for stock analysis using FastAPI.

This module implements a FastAPI server that handles LINE Bot webhook events,
processes user messages using Claude AI, and sends responses back to users
through the LINE Messaging API.
"""

import logging
import os
from typing import Dict

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from linebot.v3 import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from agents.trial_agent import Agent
from tools.analysis.analysis_tool import AnalysisTool
from tools.research.research_tool import ResearchTool
from agents.technical_analysis_agents.ta_agents import TechnicalAnalysisTool
from tools.technical_analysis.ta_tool import TATool
from agents.chip_analysis_agents.chip_agent import ChipAnalysisTool
from agents.planning_agents.planning_agent import PlanningTool

load_dotenv()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LINE Bot Stock Analysis API",
    description="FastAPI server for LINE Bot stock analysis",
    version="1.0.0",
)

configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
parser = WebhookParser(os.getenv("LINE_CHANNEL_SECRET"))

# Create async API client
async_api_client = AsyncApiClient(configuration)
line_bot_api = AsyncMessagingApi(async_api_client)

# Dictionary to store agents for each user
agent_management: Dict[str, Agent] = {}


def create_agent() -> Agent:
    """Create a new agent instance with all necessary tools."""
    agent = Agent(
        provider="anthropic",
        model_name="claude-3-5-sonnet-20240229",
        tools={},  # Empty tools dict initially
    )

    # Set up tools using the created agent
    tools = {
        "research": ResearchTool(lambda news: agent.company_news.extend(news)),
        "analysis_report": AnalysisTool(lambda: agent.company_news),
        "planning": PlanningTool(lambda: agent.company_news),
        "technical_analysis": TATool(),
        "chips_analysis": ChipAnalysisTool(),  # Changed from chip_analysis to chips_analysis
    }

    # Update agent's tools
    agent.tools = tools
    return agent


@app.post("/callback")
async def callback(request: Request):
    """Handle LINE webhook callback.

    Validates the signature and processes the webhook event.

    Args:
        request: The incoming FastAPI request

    Returns:
        str: 'OK' if successful

    Raises:
        HTTPException: 400 if signature is invalid
    """
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    body_str = body.decode()

    try:
        events = parser.parse(body_str, signature)
        for event in events:
            if isinstance(event, MessageEvent) and isinstance(
                event.message, TextMessageContent
            ):
                await handle_text_message(event)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        raise HTTPException(
            status_code=400,
            detail="Invalid signature. Please check your channel access token/channel secret.",
        )

    return "OK"


async def handle_text_message(event: MessageEvent):
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
        
        # Process message and get response
        response = await user_agent.chat(text)
        
        # Split response into chunks if too long (LINE message limit is 5000 characters)
        if len(response) > 5000:
            chunks = [response[i:i+4999] for i in range(0, len(response), 4999)]
            messages = [TextMessage(text=chunk) for chunk in chunks]
        else:
            messages = [TextMessage(text=response)]

        # Send response using async API client
        await line_bot_api.reply_message(
            ReplyMessageRequest(reply_token=event.reply_token, messages=messages)
        )

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        error_message = "處理訊息時發生錯誤，請稍後再試"
        await line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=error_message)],
            )
        )


@app.get("/")
async def home():
    """Handle requests to the root endpoint.

    Returns:
        str: A simple greeting message
    """
    return "Hello World"


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8888, reload=True)
