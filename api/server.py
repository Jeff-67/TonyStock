"""FastAPI server for TonyStock chat API.

This module implements a FastAPI server that exposes the chat_with_claude function
as a REST API endpoint.
"""

from typing import Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agents.trial_agent import chat_with_claude

# Create FastAPI app
app = FastAPI(
    title="TonyStock Chat API",
    description="API for interacting with TonyStock's chat functionality",
    version="1.0.0",
)


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    response: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Chat endpoint that processes user messages using chat_with_claude.

    Args:
        request: The chat request containing the user's message

    Returns:
        ChatResponse containing the model's response

    Raises:
        HTTPException: If there is an error processing the request
    """
    try:
        response = await chat_with_claude(request.message)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint.

    Returns:
        Dict containing status information
    """
    return {"status": "healthy"}


def start():
    """Start the FastAPI server using uvicorn."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    start()
