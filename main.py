import os
import re
import json
import autogen
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

# --------------------------
# Global Configuration & Retry Helpers
# --------------------------
"""
SIA (Support Intelligence Assistant)

This module implements a support assistant using the AutoGen framework that can handle
listing-related and brand approval queries. The assistant follows specific workflows
based on user input, making API calls and providing appropriate responses.

The system uses a custom function calling approach with a dedicated FunctionExecutor agent
to handle API interactions. Communication between agents follows a specific pattern
to ensure proper routing and execution of function calls.
"""

MAX_RETRIES = 3  # Maximum number of retry attempts for API calls
retry_counts = {}  # Dictionary to track retry counts for different API calls

# Azure OpenAI API Configuration
config_list = [{
    "model": "gpt-4o-mini",
    "api_type": "azure",
    "api_key": "YOUR_KEY_GOES_HERE",  # Replace with your secure key
    "base_url": "https://fkopenai.openai.azure.com/",
    "api_version": "2024-02-15-preview"
}]

def get_retry_count(key: str) -> int:
    """
    Get the current retry count for a specific key.
    
    Args:
        key: The identifier for the API call being tracked
        
    Returns:
        int: The current retry count (0 if not previously tracked)
    """
    return retry_counts.get(key, 0)

def increment_retry(key: str) -> int:
    """
    Increment the retry count for a specific key.
    
    Args:
        key: The identifier for the API call being tracked
        
    Returns:
        int: The updated retry count after incrementing
    """
    retry_counts[key] = get_retry_count(key) + 1
    print(f"DEBUG: Incrementing retry for {key}: {retry_counts[key]}")
    return retry_counts[key]

def reset_retries(key: str):
    """
    Reset the retry count for a specific key.
    
    Args:
        key: The identifier for the API call to reset
    """
    if key in retry_counts:
        print(f"DEBUG: Resetting retries for {key}")
        del retry_counts[key]

# --------------------------
# Function Implementations for API Calls
# --------------------------
def get_user_status(user_id: str = "default") -> dict:
    """
    Get the status of a user account.
    
    This function simulates an API call to check a user's account status.
    For user IDs starting with "5", the function simulates API failures
    that require retries. For other IDs, the function returns different
    statuses based on the ID pattern.
    
    Args:
        user_id: The ID of the user to check
        
    Returns:
        dict: A dictionary containing the user's status and associated information
            {
                "status": One of ["active", "onboarding", "on_hold", "retrying"],
                "message": Human-readable message describing the status,
                "retry_needed": (Optional) Boolean indicating if a retry is needed,
                "auto_retry": (Optional) Boolean indicating if retry should be automatic,
                "user_id": The user_id that was checked
            }
    """
    print(f"\n🔴 [get_user_status] Received user_id: '{user_id}'")
    # Retry logic if user_id starts with "5"
    if user_id.startswith("5"):
        retry_key = f"user_{user_id}"
        current_retry = increment_retry(retry_key)
        print(f"🔄 [get_user_status] Retry count for {user_id}: {current_retry} (Max: {MAX_RETRIES})")
        if current_retry < MAX_RETRIES:
            return {
                "status": "retrying",
                "message": f"Automatically retrying API call (attempt {current_retry}/{MAX_RETRIES})",
                "retry_needed": True,
                "auto_retry": True,
                "user_id": user_id
            }
        else:
            reset_retries(retry_key)
            return {
                "status": "on_hold",
                "reason_code": "MAX_RETRIES_EXCEEDED",
                "message": "Account verification failed after multiple attempts",
                "user_id": user_id
            }

    # Normal user status logic
    if user_id.startswith("1"):
        result = {
            "status": "active",
            "message": "Your account is active.",
            "user_id": user_id
        }
    elif user_id.startswith("2"):
        result = {
            "status": "onboarding",
            "message": (
                "Your products aren't visible yet. Once onboarding is complete, "
                "your account will be activated within 48 hours, and your listings "
                "will go live."
            ),
            "user_id": user_id
        }
    else:
        result = {
            "status": "on_hold",
            "message": "Your account is on hold. Please contact support if you have questions.",
            "user_id": user_id
        }
    print(f"🔵 [get_user_status] Returning: {result}")
    return result


def get_listing_status(listing_id: str = "default") -> dict:
    """
    Get the status of a product listing.
    
    This function simulates an API call to check a listing's status.
    For listing IDs starting with "5", the function simulates API failures
    that require retries. For other IDs, the function returns different
    statuses based on the last character of the ID.
    
    Args:
        listing_id: The ID of the listing to check
        
    Returns:
        dict: A dictionary containing the listing's status and associated information
            {
                "status": One of ["active", "inactive", "blocked", "archived", "rfa", "retrying", "error"],
                "message": Human-readable message describing the status,
                "block_reason": (Optional) Reason why a listing is blocked,
                "retry_needed": (Optional) Boolean indicating if a retry is needed,
                "auto_retry": (Optional) Boolean indicating if retry should be automatic,
                "listing_id": The listing_id that was checked
            }
    """
    print(f"\n🔴 [get_listing_status] Received listing_id: '{listing_id}'")
    # Retry logic if listing_id starts with "5"
    if listing_id.startswith("5"):
        retry_key = f"listing_{listing_id}"
        current_retry = increment_retry(retry_key)
        print(f"🔄 [get_listing_status] Retry count for {listing_id}: {current_retry} (Max: {MAX_RETRIES})")
        if current_retry < MAX_RETRIES:
            result = {
                "status": "retrying",
                "message": f"Automatically retrying API call (attempt {current_retry}/{MAX_RETRIES})",
                "retry_needed": True,
                "auto_retry": True,
                "listing_id": listing_id
            }
            print(f"DEBUG: [get_listing_status] Returning (auto-retry): {result}")
            return result
        else:
            reset_retries(retry_key)
            result = {
                "status": "error",
                "message": "Maximum retries reached for listing. Terminating conversation. Please try again later. TERMINATE",
                "retry_needed": False,
                "listing_id": listing_id
            }
            print(f"DEBUG: [get_listing_status] Returning (max retries reached): {result}")
            return result

    # Normal listing status logic
    last_char = listing_id[-1] if listing_id else "0"
    if last_char == "2":
        result = {
            "status": "blocked",
            "message": "Your listing is blocked due to seller state change.",
            "block_reason": "seller_state_change",
            "listing_id": listing_id
        }
    elif last_char == "1":
        result = {
            "status": "inactive",
            "message": "Your listing is currently inactive. Please activate it to be visible.",
            "listing_id": listing_id
        }
    elif last_char == "3":
        result = {
            "status": "archived",
            "message": "Your listing is archived and not visible to customers.",
            "listing_id": listing_id
        }
    elif last_char == "4":
        result = {
            "status": "rfa",
            "message": "Your listing is pending approval (RFA).",
            "listing_id": listing_id
        }
    else:
        result = {
            "status": "active",
            "message": "Your listing is active and visible to customers.",
            "listing_id": listing_id
        }
    print(f"DEBUG: [get_listing_status] Returning: {result}")
    return result


def can_reactivate_listing(block_reason: str) -> dict:
    """
    Check if a blocked listing can be reactivated.
    
    This function simulates an API call to determine whether a blocked 
    listing can be reactivated based on the block reason.
    
    Args:
        block_reason: The reason why the listing is blocked
        
    Returns:
        dict: A dictionary indicating whether reactivation is possible
            {
                "can_reactivate": Boolean indicating if reactivation is possible,
                "message": Human-readable message with the result
            }
    """
    print(f"\n🔴 [can_reactivate_listing] Received block_reason: '{block_reason}'")
    result = {"can_reactivate": True, "message": "Listing can be reactivated."}
    print(f"🔵 [can_reactivate_listing] Returning: {result}")
    return result


def create_support_ticket(user_id: str, listing_id: str, reason: str) -> dict:
    """
    Create a support ticket for a user regarding a specific listing.
    
    This function simulates an API call to create a support ticket in the
    customer service system. It generates a ticket ID and confirmation message.
    
    Args:
        user_id: The ID of the user creating the ticket
        listing_id: The ID of the listing related to the ticket (or "N/A")
        reason: The reason for creating the support ticket
        
    Returns:
        dict: A dictionary containing the ticket details
            {
                "ticket_id": The generated ticket ID,
                "status": The status of the ticket creation ("created"),
                "message": Human-readable confirmation message
            }
    """
    print(f"\n🔴 [create_support_ticket] Received user_id: '{user_id}', listing_id: '{listing_id}', reason: '{reason}'")
    result = {
        "ticket_id": "TICKET12345",
        "status": "created",
        "message": f"Support ticket created for user {user_id} regarding listing {listing_id}: {reason}"
    }
    print(f"🔵 [create_support_ticket] Returning: {result}")
    return result


# --------------------------
# New function for brand approval
# --------------------------
def get_brand_approval_status(request_id: str = "default") -> dict:
    """
    Get the status of a brand approval request.
    
    This function simulates an API call to check the status of a brand approval request.
    It returns different statuses based on the last character of the request_id.
    
    Args:
        request_id: The ID of the brand approval request to check
        
    Returns:
        dict: A dictionary containing the brand approval status and timeline
            {
                "status": One of ["approved", "in_progress", "disapproved"],
                "message": Human-readable message describing the status,
                "timeline_hours": (Optional) Expected time to completion in hours
            }
    """
    print(f"\n🔴 [get_brand_approval_status] Received request_id: '{request_id}'")

    last_char = request_id[-1] if request_id else "0"
    if last_char == "1":
        result = {
            "status": "approved",
            "message": "Your brand approval request is approved."
        }
    elif last_char == "2":
        result = {
            "status": "in_progress",
            "message": "Brand approval is still in progress.",
            "timeline_hours": 48
        }
    else:
        result = {
            "status": "disapproved",
            "message": "Brand approval disapproved. Additional steps required.",
            "timeline_hours": 80
        }
    print(f"🔵 [get_brand_approval_status] Returning: {result}")
    return result


# --------------------------
# Function Call Execution via FunctionExecutor
# --------------------------
class FunctionExecutorAgent(UserProxyAgent):
    """
    A specialized agent that executes function calls made by the SIA agent.
    
    This agent extends the UserProxyAgent class to intercept messages from the SIA
    agent that follow the FUNCTION_CALL format, execute the corresponding function,
    and return the result.
    
    The agent only responds to properly formatted function calls and ignores other messages.
    """
    def generate_reply(self, messages=None, sender=None, **kwargs):
        """
        Generate a reply based on the messages received.
        
        This method overrides the parent class method to intercept and process
        function calls in the specific format FUNCTION_CALL:<name>{<params>}.
        
        Args:
            messages: List of messages to process
            sender: The agent that sent the messages
            **kwargs: Additional arguments
            
        Returns:
            dict with "content" key containing the function result, or None if no function call found
        """
        if messages is None:
            messages = self._oai_messages[sender]
        print(f"DEBUG [FunctionExecutor] Received messages from {sender.name}:")
        for m in messages:
            print("   ", m.get("content", ""))

        # We only check SIA's last message for function calls
        sia_msgs = [m for m in messages if m.get("name") == "SIA"]
        if not sia_msgs:
            return None

        last_msg = sia_msgs[-1].get("content", "")
        print(f"DEBUG [FunctionExecutor] Checking SIA message: {last_msg}")

        # Strict regex to detect function call
        if re.search(r'^\s*FUNCTION_CALL:\w+\s*\{.*\}\s*$', last_msg, re.DOTALL):
            print("🔧 [FunctionExecutor] Detected valid function call format")
            return {"content": execute_function_call(last_msg)}
        else:
            print("⚠️ [FunctionExecutor] No valid function call detected")
            return None


def execute_function_call(message: str) -> str:
    """
    Parse and execute a function call message.
    
    This function takes a message in the format FUNCTION_CALL:<name>{<params>},
    extracts the function name and parameters, executes the corresponding function,
    and returns the result as a JSON string.
    
    Args:
        message: The function call message to execute
        
    Returns:
        str: JSON-encoded result of the function call or error message
    """
    print(f"\n🔍 [execute_function_call] RAW INPUT:\n{message}\n{'='*50}")
    try:
        pattern = r'^\s*FUNCTION_CALL:(\w+)\s*(\{.*\})\s*$'
        match = re.search(pattern, message, re.DOTALL)
        if not match:
            error_msg = "❌ [execute_function_call] INVALID FORMAT - Missing FUNCTION_CALL: prefix or malformed parameters"
            print(error_msg)
            return json.dumps({"status": "error", "message": error_msg})

        func_name, params_str = match.groups()
        print(f"✅ [execute_function_call] PARSED - Function: {func_name}, Params: {params_str}")

        try:
            params = json.loads(params_str)
            print(f"🔧 [execute_function_call] VALIDATED PARAMS: {json.dumps(params, indent=2)}")
        except json.JSONDecodeError as e:
            error_msg = f"❌ [execute_function_call] INVALID JSON: {str(e)}"
            print(error_msg)
            return json.dumps({"status": "error", "message": error_msg})

        # Dispatch the correct function
        if func_name == "get_user_status":
            result = get_user_status(params.get("user_id", "default"))
        elif func_name == "get_listing_status":
            result = get_listing_status(params.get("listing_id", "default"))
        elif func_name == "can_reactivate_listing":
            result = can_reactivate_listing(params.get("block_reason", ""))
        elif func_name == "create_support_ticket":
            result = create_support_ticket(
                params.get("user_id", ""),
                params.get("listing_id", ""),
                params.get("reason", "")
            )
        elif func_name == "get_brand_approval_status":
            result = get_brand_approval_status(params.get("request_id", ""))
        else:
            error_msg = f"❌ [execute_function_call] UNKNOWN FUNCTION: {func_name}"
            print(error_msg)
            return json.dumps({"status": "error", "message": error_msg})

        print(f"✅ [execute_function_call] SUCCESS - Result:\n{json.dumps(result, indent=2)}")
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        error_msg = f"‼️ [execute_function_call] CRITICAL ERROR: {str(e)}"
        print(error_msg)
        return json.dumps({
            "status": "critical_error",
            "message": "System failure - contact support",
            "technical_details": error_msg
        })


# --------------------------
# Instantiate FunctionExecutor Agent
# --------------------------
function_executor = FunctionExecutorAgent(
    name="FunctionExecutor",
    human_input_mode="NEVER",
    system_message="EXCLUSIVELY executes valid function calls in FUNCTION_CALL: format",
    code_execution_config={
        "last_n_messages": 2,
        "work_dir": "groupchat",
        "use_docker": False
    }
)
function_executor.register_function({"execute_function_call": execute_function_call})
function_executor.register_function({
    "get_user_status": get_user_status,
    "get_listing_status": get_listing_status,
    "can_reactivate_listing": can_reactivate_listing,
    "create_support_ticket": create_support_ticket,
    "get_brand_approval_status": get_brand_approval_status  # <--- new brand function
})

# --------------------------
# Define Other Agents
# --------------------------
user_agent = UserProxyAgent(
    name="User",
    human_input_mode="ALWAYS",
    system_message="You are a human user interacting with the support system.",
    code_execution_config=False
)

coordinator = AssistantAgent(
    name="Coordinator",
    system_message="""ORCHESTRATION RULES:
1. If SIA requests user ID → Select User as next speaker.
2. If FunctionExecutor returns results → Select SIA as next speaker.
3. If error occurs → Terminate the conversation.
4. Else → Continue normal rotation.
""",
    llm_config={"config_list": config_list}
)

# --------------------------
# Unified SIA System Message
# Handling both listing logic and brand approval logic
# --------------------------
sia = AssistantAgent(
    name="SIA",
    system_message="""
You are a support assistant that can handle both listing-related queries and brand approval queries.
TEMPLATING AND STATUS COMMUNICATION:

1. If the user wants listing help:
   - Ask for user ID using: FUNCTION_CALL:get_user_status{"user_id": "$0"}
   - After user status response:
       • IF status is "retrying" and auto_retry is true:
         OUTPUT: FUNCTION_CALL:get_user_status{"user_id": "$user_id"}
       • IF status is "active":
         OUTPUT: "[message from response] Please provide listing ID."
       • IF status is "onboarding":
         OUTPUT: "[message from response] TERMINATING chat now. TERMINATE"
       • IF status is "on_hold":
         OUTPUT: "[message from response] Please provide listing ID."
       • ELSE:
         OUTPUT: "[message from response] Please provide listing ID."
   - For listing ID input, use: FUNCTION_CALL:get_listing_status{"listing_id": "$0"}
   - After listing status response:
       • IF status is "retrying" and auto_retry is true:
         OUTPUT: FUNCTION_CALL:get_listing_status{"listing_id": "$listing_id"}
       • IF status is "active" or "inactive":
         OUTPUT: "[message from response] Inform the user that their listing is active/inactive. TERMINATE"
       • IF status is "blocked":
         OUTPUT: "FUNCTION_CALL:create_support_ticket{\"user_id\": \"$user_id\", \"listing_id\": \"$listing_id\", \"reason\": \"Reactivation requested\"}"
       • IF status is "archived":
         OUTPUT: "[message from response] This listing is archived and cannot be reactivated. TERMINATE"
       • IF status is "rfa":
         OUTPUT: "[message from response] Your listing is pending approval. TERMINATE"
       • IF status is "error" (with retry_needed false):
         OUTPUT: "[message from response] Terminating conversation. Please try again later. TERMINATE"

2. If the user wants brand approval:
   - Ask for the brand request ID using: FUNCTION_CALL:get_brand_approval_status{"request_id": "$0"}
   - After brand approval status response:
       • IF status is "approved":
         OUTPUT: "[message from response] Your brand approval request is approved. TERMINATE"
       • IF status is "in_progress" or "disapproved":
           - IF timeline_hours <= 72:
             OUTPUT: "[message from response] Please wait while your brand request is processed. TERMINATE"
           - ELSE:
             OUTPUT: "FUNCTION_CALL:create_support_ticket{\"user_id\": \"$user_id\", \"listing_id\": \"N/A\", \"reason\": \"Brand approval follow-up\"}"
   - After support ticket response for brand approval:
       • IF status is "created":
         OUTPUT: "[message from response] Support ticket $ticket_id created for brand approval. TERMINATE"

3. Use EXACT function call formats:
   - FUNCTION_CALL:get_user_status{"user_id": "[ID]"}
   - FUNCTION_CALL:get_listing_status{"listing_id": "[ID]"}
   - FUNCTION_CALL:create_support_ticket{"user_id": "[USER_ID]", "listing_id": "[LISTING_ID]", "reason": "[REASON]"}
   - FUNCTION_CALL:get_brand_approval_status{"request_id": "[REQUEST_ID]"}

4. Always end the conversation with 'TERMINATE' if no further steps are needed.

5. Retry logic remains the same for IDs that start with '5' (the system will handle auto-retry).

""",
    llm_config={"config_list": config_list}
)



# --------------------------
# Custom Speaker Selection
# --------------------------
class CustomGroupChat(GroupChat):
    """
    Custom implementation of the GroupChat class with a specialized speaker selection method.
    
    This class overrides the default speaker selection logic to implement a custom
    turn-taking system that ensures proper routing of messages between agents.
    """
    def select_speaker(self, last_speaker, selector):
        """
        Select the next speaker in the conversation.
        
        This method delegates to the speaker_selection_func to determine
        which agent should speak next based on the current conversation state.
        
        Args:
            last_speaker: The agent that spoke last
            selector: The agent responsible for selecting the next speaker
            
        Returns:
            The next agent to speak, or None to terminate the conversation
        """
        return speaker_selection_func(last_speaker, self)

def speaker_selection_func(last_speaker, groupchat):
    """
    Custom speaker selection logic for the group chat.
    
    This function implements rules to determine which agent should speak next
    based on the current conversation state, message content, and sender.
    
    Args:
        last_speaker: The agent that spoke last
        groupchat: The GroupChat instance
        
    Returns:
        The next agent to speak, or None to terminate the conversation
    """
    messages = groupchat.messages
    if not messages:
        return next(agent for agent in groupchat.agents if agent.name == "SIA")

    last_msg = messages[-1]
    content = last_msg.get("content", "")
    sender = last_msg.get("name", "")

    # Check for termination condition: message ends with TERMINATE
    if content.rstrip().endswith("TERMINATE"):
        print("DEBUG: Termination condition met in message. Chat will be terminated.")
        return None

    print("DEBUG: Last speaker was", sender, "content:", content[:50] if len(content) > 50 else content)

    # If SIA just output a function call => next is FunctionExecutor
    if sender == "SIA" and re.search(r'^\s*FUNCTION_CALL:\w+\s*\{.*\}\s*$', content, re.DOTALL):
        print("DEBUG: SIA issued function call -> FunctionExecutor will process")
        return next(agent for agent in groupchat.agents if agent.name == "FunctionExecutor")

    # If SIA just gave a normal prompt => next is User
    if sender == "SIA" and "FUNCTION_CALL:" not in content:
        print("DEBUG: SIA sent a prompt -> User will respond")
        return next(agent for agent in groupchat.agents if agent.name == "User")

    # If FunctionExecutor just returned a result => back to SIA
    if sender == "FunctionExecutor":
        print("DEBUG: FunctionExecutor returned result -> SIA will interpret")
        return next(agent for agent in groupchat.agents if agent.name == "SIA")

    # If the last speaker is User => SIA responds
    if sender == "User":
        print("DEBUG: User sent a message -> SIA will respond")
        return next(agent for agent in groupchat.agents if agent.name == "SIA")

    print("DEBUG: Default fallback -> User will respond")
    return next(agent for agent in groupchat.agents if agent.name == "User")


# --------------------------
# Setup Custom Group Chat and Manager
# --------------------------
groupchat = CustomGroupChat(
    agents=[user_agent, sia, function_executor, coordinator],
    messages=[],
    max_round=25,
    speaker_selection_method="round_robin",  # Ignored by our custom speaker selection
    allow_repeat_speaker=False,
    func_call_filter=True
)

manager = GroupChatManager(
    groupchat=groupchat,
    llm_config={
        "config_list": config_list,
        "temperature": 0,
        "timeout": 120
    },
    is_termination_msg=lambda msg: msg.get("content", "").rstrip().endswith("TERMINATE")
)

# --------------------------
# Start Chat Session
# --------------------------
def start_chat():
    """
    Start a new chat session with the SIA assistant.
    
    This function initializes the chat with a standard opening message
    and begins the conversation flow. It handles the entire chat session
    until termination.
    """
    print("\n🔍 DEBUG: Starting new chat session")
    print("DEBUG: Agent order:", [a.name for a in groupchat.agents])
    print("DEBUG: SIA system message:\n", sia.system_message)
    try:
        print("DEBUG: Initiating chat with message: 'I need help with my listing or brand approval'")
        user_agent.initiate_chat(
            manager,
            message="I need help with my listing or brand approval",
            clear_history=True
        )
    except Exception as e:
        print(f"🔴 CRITICAL ERROR: {str(e)}")
        raise


if __name__ == "__main__":
    start_chat()
