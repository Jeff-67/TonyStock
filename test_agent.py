import anthropic
from tools.search_engine import search
from prompts.system_prompts import tool_prompt_construct_anthropic, system_prompt
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from settings import Settings
import json
from opik import track

client = anthropic.Client()
settings = Settings()
MODEL_NAME = settings.model.claude_small
MAX_SEARCH_RESULTS = 5

@dataclass
class ToolExecutionResult:
    success: bool
    tool_name: str
    result: Optional[Any] = None
    message: str = ""

@dataclass
class VerificationResult:
    success: bool
    message: str
    formatted_result: Optional[str] = None

@dataclass
class ModelResponse:
    stop_reason: str
    content: List[Any]
    tool_use: Optional[Dict[str, Any]] = None
    text_content: Optional[str] = None

@track()
def process_model_response(response: anthropic.types.Message) -> ModelResponse:
    """Process the raw model response into a structured format.
    Args:
        response: Raw response from the model
    Returns:
        ModelResponse containing structured response data
    """
    text_content = next((block.text for block in response.content if hasattr(block, "text")), None)
    tool_use = next((block for block in response.content if block.type == "tool_use"), None)
    
    return ModelResponse(
        stop_reason=response.stop_reason,
        content=response.content,
        tool_use=tool_use,
        text_content=text_content
    )

@track()
def call_model(messages: List[Dict[str, Any]], system_msg: bool = False) -> ModelResponse:
    """Make an API call to the model.
    Args:
        messages: List of message objects to send
        system_msg: Whether to include system prompt
    Returns:
        ModelResponse containing the processed response
    """
    if system_msg:
        messages[0]["content"] = system_prompt(model_name=MODEL_NAME) + "\nCurrent User Message: " + messages[0]["content"]
    
    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=settings.max_tokens,
        tools=tool_prompt_construct_anthropic()["tools"],
        messages=messages
    )
    
    return process_model_response(response)

@track()
def process_tool_call(tool_name: str, tool_input: Dict[str, Any]) -> Any:
    """Process a tool call and return the result."""
    try:
        if tool_name == "search_engine":
            return search(tool_input["query"], max_results=MAX_SEARCH_RESULTS)
        else:
            return f"Unknown tool: {tool_name}"
    except Exception as e:
        return f"Tool execution failed: {str(e)}"

@track()
def verify_tool_result(tool_name: str, result: Any) -> VerificationResult:
    """Verify and format tool results."""
    if isinstance(result, str) and ("failed" in result.lower() or "unknown" in result.lower()):
        return VerificationResult(success=False, message=result)
        
    if tool_name == "search_engine":
        if not isinstance(result, list):
            return VerificationResult(
                success=False,
                message="Search engine should return a list of results"
            )
            
        if not result:
            return VerificationResult(
                success=False,
                message="Search returned no results"
            )
            
        # Format search results
        formatted_results = []
        for item in result:
            title = item.get('title', 'No Title')
            snippet = item.get('snippet', 'No Content')
            url = item.get('url', 'No URL')
            
            formatted_result = (
                f"Source: {title}\n"
                f"URL: {url}\n"
                f"Summary: {snippet}"
            )
            formatted_results.append(formatted_result)
            
        return VerificationResult(
            success=True,
            message=f"Found {len(result)} results",
            formatted_result="\n\n---\n\n".join(formatted_results)
        )
    
    return VerificationResult(
        success=True,
        message="Tool executed successfully",
        formatted_result=str(result)
    )


@track(project_name="tony_stock")
def chat_with_claude(user_message: str) -> str:
    """Main function to handle the chat flow with tool usage."""
    # Initial call with system prompt
    response = call_model([{"role": "user", "content": user_message}], system_msg=True)

    while response.stop_reason == "tool_use" and response.tool_use:
        tool_name = response.tool_use.name
        tool_input = response.tool_use.input

        # Execute tool
        tool_result = process_tool_call(tool_name, tool_input)

        # Verify and format result
        verification = verify_tool_result(tool_name, tool_result)
        
        if not verification.success:
            print(f"Tool execution failed: {verification.message}")
            break

        # Continue conversation with verified result
        messages = [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": response.content},
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": response.tool_use.id,
                        "content": verification.formatted_result,
                    }
                ],
            },
        ]

        response = call_model(messages)

    return response.text_content or "No response generated"

if __name__ == "__main__":
    chat_with_claude("What is the stock market in Tokyo?, search_engine search it")