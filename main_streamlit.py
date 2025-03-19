"""
Support Intelligence Assistant (SIA) - Streamlit Interface

This module implements a web-based interface for the Support Intelligence Assistant using Streamlit.
It provides a user-friendly interface for interacting with the SIA system, handling both listing-related
and brand approval queries. The interface includes features like chat history, user context tracking,
and real-time status updates.

The module extends the core SIA functionality from main.py with a web-based UI, adding features like:
- Interactive chat interface
- Configuration sidebar
- Session state management
- Debug information display
- Quick testing inputs
"""

import os
import re
import json
import streamlit as st
import autogen
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
import time
from typing import List, Dict, Any, Optional

# Set page config
st.set_page_config(
    page_title="Support Intelligence Assistant (SIA)",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------
# Global Configuration & Retry Helpers
# --------------------------
MAX_RETRIES = 3  # Maximum number of retry attempts for API calls
retry_counts = {}  # Dictionary to track retry counts for different API calls

# Add sidebar for configuration
st.sidebar.title("⚙️ Configuration")

# API configuration in sidebar with proper secret handling
api_key = st.sidebar.text_input("Azure OpenAI API Key", value="9222bde64b194310b1aadcff3ae5b60b", type="password")
base_url = st.sidebar.text_input("Base URL", value="https://fkopenai.openai.azure.com/")
api_version = st.sidebar.text_input("API Version", value="2024-02-15-preview")
model = st.sidebar.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-4"], index=0)

# Initialize session state for conversation history if it doesn't exist
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'user_context' not in st.session_state:
    st.session_state.user_context = {
        "user_id": None,
        "listing_id": None,
        "request_id": None
    }

if 'is_initialized' not in st.session_state:
    st.session_state.is_initialized = False

if 'is_chat_active' not in st.session_state:
    st.session_state.is_chat_active = True

# Create config list with user inputs
config_list = [{
    "model": model,
    "api_type": "azure",
    "api_key": api_key,
    "base_url": base_url,
    "api_version": api_version
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
    Increment the retry count for a specific key and update the UI.
    
    Args:
        key: The identifier for the API call being tracked
        
    Returns:
        int: The updated retry count after incrementing
    """
    retry_counts[key] = get_retry_count(key) + 1
    st.sidebar.write(f"🔄 Retry attempt: {retry_counts[key]}/{MAX_RETRIES}")
    return retry_counts[key]

def reset_retries(key: str):
    """
    Reset the retry count for a specific key.
    
    Args:
        key: The identifier for the API call to reset
    """
    if key in retry_counts:
        del retry_counts[key]

# --------------------------
# Function Implementations for API Calls
# --------------------------
def get_user_status(user_id: str = "default") -> dict:
    """
    Get the status of a user account with UI feedback.
    
    This function simulates an API call to check a user's account status,
    providing visual feedback through Streamlit's status component.
    
    Args:
        user_id: The ID of the user to check
        
    Returns:
        dict: A dictionary containing the user's status and associated information
    """
    with st.status(f"Checking user status for ID: {user_id}...", expanded=False) as status:
        # Retry logic if user_id starts with "5"
        if user_id.startswith("5"):
            retry_key = f"user_{user_id}"
            current_retry = increment_retry(retry_key)
            status.update(label=f"Retrying user status check ({current_retry}/{MAX_RETRIES})...")
            time.sleep(1)  # Simulate API delay
            
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
                status.update(label="User verification failed after multiple attempts", state="error")
                return {
                    "status": "on_hold",
                    "reason_code": "MAX_RETRIES_EXCEEDED",
                    "message": "Account verification failed after multiple attempts",
                    "user_id": user_id
                }

        # Normal user status logic
        time.sleep(1)  # Simulate API delay
        if user_id.startswith("1"):
            status.update(label="Account is active", state="complete")
            result = {
                "status": "active",
                "message": "Your account is active.",
                "user_id": user_id
            }
        elif user_id.startswith("2"):
            status.update(label="Account is in onboarding state", state="complete")
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
            status.update(label="Account is on hold", state="complete")
            result = {
                "status": "on_hold",
                "message": "Your account is on hold. Please contact support if you have questions.",
                "user_id": user_id
            }
        return result


def get_listing_status(listing_id: str = "default") -> dict:
    """
    Get the status of a product listing with UI feedback.
    
    This function simulates an API call to check a listing's status,
    providing visual feedback through Streamlit's status component.
    
    Args:
        listing_id: The ID of the listing to check
        
    Returns:
        dict: A dictionary containing the listing's status and associated information
    """
    with st.status(f"Checking listing status for ID: {listing_id}...", expanded=False) as status:
        # Retry logic if listing_id starts with "5"
        if listing_id.startswith("5"):
            retry_key = f"listing_{listing_id}"
            current_retry = increment_retry(retry_key)
            status.update(label=f"Retrying listing status check ({current_retry}/{MAX_RETRIES})...")
            time.sleep(1)  # Simulate API delay
            
            if current_retry < MAX_RETRIES:
                return {
                    "status": "retrying",
                    "message": f"Automatically retrying API call (attempt {current_retry}/{MAX_RETRIES})",
                    "retry_needed": True,
                    "auto_retry": True,
                    "listing_id": listing_id
                }
            else:
                reset_retries(retry_key)
                status.update(label="Maximum retries reached for listing", state="error")
                return {
                    "status": "error",
                    "message": "Maximum retries reached for listing. Terminating conversation. Please try again later. TERMINATE",
                    "retry_needed": False,
                    "listing_id": listing_id
                }

        # Normal listing status logic
        time.sleep(1)  # Simulate API delay
        last_char = listing_id[-1] if listing_id else "0"
        
        if last_char == "2":
            status.update(label="Listing is blocked", state="error")
            result = {
                "status": "blocked",
                "message": "Your listing is blocked due to seller state change.",
                "block_reason": "seller_state_change",
                "listing_id": listing_id
            }
        elif last_char == "1":
            status.update(label="Listing is inactive", state="complete")
            result = {
                "status": "inactive",
                "message": "Your listing is currently inactive. Please activate it to be visible.",
                "listing_id": listing_id
            }
        elif last_char == "3":
            status.update(label="Listing is archived", state="complete")
            result = {
                "status": "archived",
                "message": "Your listing is archived and not visible to customers.",
                "listing_id": listing_id
            }
        elif last_char == "4":
            status.update(label="Listing is pending approval", state="complete")
            result = {
                "status": "rfa",
                "message": "Your listing is pending approval (RFA).",
                "listing_id": listing_id
            }
        else:
            status.update(label="Listing is active", state="complete")
            result = {
                "status": "active",
                "message": "Your listing is active and visible to customers.",
                "listing_id": listing_id
            }
        return result


def can_reactivate_listing(block_reason: str) -> dict:
    """
    Check if a blocked listing can be reactivated with UI feedback.
    
    Args:
        block_reason: The reason why the listing is blocked
        
    Returns:
        dict: A dictionary indicating whether reactivation is possible
    """
    with st.status(f"Checking if listing can be reactivated...", expanded=False) as status:
        time.sleep(1)  # Simulate API delay
        status.update(label="Listing can be reactivated", state="complete")
        return {"can_reactivate": True, "message": "Listing can be reactivated."}


def create_support_ticket(user_id: str, listing_id: str, reason: str) -> dict:
    """
    Create a support ticket with UI feedback.
    
    Args:
        user_id: The ID of the user creating the ticket
        listing_id: The ID of the listing related to the ticket
        reason: The reason for creating the support ticket
        
    Returns:
        dict: A dictionary containing the ticket details
    """
    with st.status(f"Creating support ticket...", expanded=False) as status:
        time.sleep(2)  # Simulate API delay
        ticket_id = "TICKET" + str(int(time.time()))[-5:]
        status.update(label=f"Support ticket {ticket_id} created", state="complete")
        return {
            "ticket_id": ticket_id,
            "status": "created",
            "message": f"Support ticket created for user {user_id} regarding listing {listing_id}: {reason}"
        }


def get_brand_approval_status(request_id: str = "default") -> dict:
    """
    Get the status of a brand approval request with UI feedback.
    
    Args:
        request_id: The ID of the brand approval request to check
        
    Returns:
        dict: A dictionary containing the brand approval status and timeline
    """
    with st.status(f"Checking brand approval status for request ID: {request_id}...", expanded=False) as status:
        time.sleep(1)  # Simulate API delay
        
        last_char = request_id[-1] if request_id else "0"
        if last_char == "1":
            status.update(label="Brand approval request is approved", state="complete")
            result = {
                "status": "approved",
                "message": "Your brand approval request is approved."
            }
        elif last_char == "2":
            status.update(label="Brand approval is in progress", state="complete")
            result = {
                "status": "in_progress",
                "message": "Brand approval is still in progress.",
                "timeline_hours": 48
            }
        else:
            status.update(label="Brand approval is disapproved", state="error")
            result = {
                "status": "disapproved",
                "message": "Brand approval disapproved. Additional steps required.",
                "timeline_hours": 80
            }
        return result


# --------------------------
# Function Call Execution via FunctionExecutor
# --------------------------
class FunctionExecutorAgent(UserProxyAgent):
    """
    A specialized agent that executes function calls made by the SIA agent.
    Extends UserProxyAgent to handle function calls in the Streamlit interface.
    """
    def generate_reply(self, messages=None, sender=None, **kwargs):
        """
        Generate a reply based on the messages received.
        
        Args:
            messages: List of messages to process
            sender: The agent that sent the messages
            **kwargs: Additional arguments
            
        Returns:
            dict with "content" key containing the function result, or None if no function call found
        """
        if messages is None:
            messages = self._oai_messages[sender]

        # We only check SIA's last message for function calls
        sia_msgs = [m for m in messages if m.get("name") == "SIA"]
        if not sia_msgs:
            return None

        last_msg = sia_msgs[-1].get("content", "")

        # Strict regex to detect function call
        if re.search(r'^\s*FUNCTION_CALL:\w+\s*\{.*\}\s*$', last_msg, re.DOTALL):
            return {"content": execute_function_call(last_msg)}
        else:
            return None


def execute_function_call(message: str) -> str:
    """
    Parse and execute a function call message.
    
    Args:
        message: The function call message to execute
        
    Returns:
        str: JSON-encoded result of the function call or error message
    """
    try:
        pattern = r'^\s*FUNCTION_CALL:(\w+)\s*(\{.*\})\s*$'
        match = re.search(pattern, message, re.DOTALL)
        if not match:
            error_msg = "Invalid function call format"
            return json.dumps({"status": "error", "message": error_msg})

        func_name, params_str = match.groups()

        try:
            params = json.loads(params_str)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON parameters: {str(e)}"
            return json.dumps({"status": "error", "message": error_msg})

        # Dispatch the correct function
        if func_name == "get_user_status":
            # Save the user_id to session state
            user_id = params.get("user_id", "default")
            st.session_state.user_context["user_id"] = user_id
            result = get_user_status(user_id)
        elif func_name == "get_listing_status":
            # Save the listing_id to session state
            listing_id = params.get("listing_id", "default")
            st.session_state.user_context["listing_id"] = listing_id
            result = get_listing_status(listing_id)
        elif func_name == "can_reactivate_listing":
            result = can_reactivate_listing(params.get("block_reason", ""))
        elif func_name == "create_support_ticket":
            result = create_support_ticket(
                params.get("user_id", ""),
                params.get("listing_id", ""),
                params.get("reason", "")
            )
        elif func_name == "get_brand_approval_status":
            # Save the request_id to session state
            request_id = params.get("request_id", "default")
            st.session_state.user_context["request_id"] = request_id
            result = get_brand_approval_status(request_id)
        else:
            error_msg = f"Unknown function: {func_name}"
            return json.dumps({"status": "error", "message": error_msg})

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        error_msg = f"Critical error: {str(e)}"
        return json.dumps({
            "status": "critical_error",
            "message": "System failure - contact support",
            "technical_details": error_msg
        })


# --------------------------
# Initialize agents and chat configuration
# --------------------------
def initialize_chat():
    """
    Initialize the chat session with all necessary agents and configurations.
    This function sets up the chat environment and initializes the conversation.
    """
    # Reset session state for a new chat
    st.session_state.conversation_history = []
    st.session_state.user_context = {
        "user_id": None,
        "listing_id": None,
        "request_id": None
    }
    st.session_state.is_chat_active = True
    
    # Create the function executor agent
    function_executor = FunctionExecutorAgent(
        name="FunctionExecutor",
        human_input_mode="NEVER",
        system_message="EXCLUSIVELY executes valid function calls in FUNCTION_CALL: format",
        code_execution_config={
            "last_n_messages": 2,
            "work_dir": "temp",
            "use_docker": False
        }
    )
    function_executor.register_function({"execute_function_call": execute_function_call})
    function_executor.register_function({
        "get_user_status": get_user_status,
        "get_listing_status": get_listing_status,
        "can_reactivate_listing": can_reactivate_listing,
        "create_support_ticket": create_support_ticket,
        "get_brand_approval_status": get_brand_approval_status
    })

    # Create a user proxy agent that will send user messages
    user_agent = UserProxyAgent(
        name="User",
        human_input_mode="NEVER",  # We'll manually provide input through Streamlit
        system_message="You are a human user interacting with the support system.",
        code_execution_config=False
    )

    # Create the SIA agent with the same system message as the original
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

    # Create a coordinator agent
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

    # Setup custom group chat
    class CustomGroupChat(GroupChat):
        """
        Custom implementation of the GroupChat class with a specialized speaker selection method.
        """
        def select_speaker(self, last_speaker, selector):
            return speaker_selection_func(last_speaker, self)

    def speaker_selection_func(last_speaker, groupchat):
        """
        Custom speaker selection logic for the group chat.
        
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
        if content and content.rstrip().endswith("TERMINATE"):
            st.session_state.is_chat_active = False
            print("CONVERSATION TERMINATED: Message contained TERMINATE marker")
            return None

        # If SIA just output a function call => next is FunctionExecutor
        if sender == "SIA" and content and re.search(r'^\s*FUNCTION_CALL:\w+\s*\{.*\}\s*$', content, re.DOTALL):
            print(f"SPEAKER SELECTION: SIA -> FunctionExecutor (function call detected)")
            return next(agent for agent in groupchat.agents if agent.name == "FunctionExecutor")

        # If SIA just gave a normal prompt => next is User
        if sender == "SIA" and content and "FUNCTION_CALL:" not in content:
            print(f"SPEAKER SELECTION: SIA -> User (normal message)")
            return next(agent for agent in groupchat.agents if agent.name == "User")

        # If FunctionExecutor just returned a result => back to SIA
        if sender == "FunctionExecutor" and content:
            print(f"SPEAKER SELECTION: FunctionExecutor -> SIA")
            return next(agent for agent in groupchat.agents if agent.name == "SIA")

        # If the last speaker is User => SIA responds
        if sender == "User" and content:
            print(f"SPEAKER SELECTION: User -> SIA")
            return next(agent for agent in groupchat.agents if agent.name == "SIA")

        # Default fallback
        print(f"SPEAKER SELECTION: Default fallback to User")
        return next(agent for agent in groupchat.agents if agent.name == "User")

    # Setup the actual GroupChat instance
    groupchat = CustomGroupChat(
        agents=[user_agent, sia, function_executor, coordinator],
        messages=[],
        max_round=25,
        speaker_selection_method="round_robin",  # Ignored by our custom speaker selection
        allow_repeat_speaker=False,
        func_call_filter=True
    )

    # Setup the GroupChatManager
    manager = GroupChatManager(
        groupchat=groupchat,
        llm_config={
            "config_list": config_list,
            "temperature": 0,
            "timeout": 120
        },
        is_termination_msg=lambda msg: msg.get("content", "").rstrip().endswith("TERMINATE")
    )
    
    st.session_state.manager = manager
    st.session_state.user_agent = user_agent
    st.session_state.is_initialized = True
    
    # Initiate conversation with standard opening message
    try:
        print("\nINITIATING NEW CONVERSATION")
        # Set up the initial conversation messages
        st.session_state.conversation_history = [
            {"role": "assistant", "content": "Hello! I'm SIA, your Support Intelligence Assistant. How can I help you today? I can assist with listing issues or brand approval requests."}
        ]
        
        # This simulates the initial message from main.py
        initial_msg = "I need help with my listing or brand approval"
        print(f"SENDING INITIAL MESSAGE: '{initial_msg}'")
        
        user_agent.initiate_chat(
            manager,
            message=initial_msg,
            clear_history=True
        )
        
        # Extract SIA's first response from the conversation
        if hasattr(manager, 'groupchat') and manager.groupchat.messages:
            # Find the first non-function-call message from SIA
            for msg in manager.groupchat.messages:
                if msg.get("name") == "SIA" and "content" in msg:
                    content = msg.get("content", "")
                    if not content.startswith("FUNCTION_CALL:"):
                        # Add initial prompt and SIA's response to the conversation history
                        print(f"INITIAL SIA RESPONSE: {content}")
                        st.session_state.conversation_history = [
                            {"role": "user", "content": initial_msg},
                            {"role": "assistant", "content": content}
                        ]
                        break
        
        print("INITIALIZATION COMPLETE")
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR DURING INITIALIZATION: {error_msg}")
        st.error(f"Error initializing chat: {error_msg}")
        # Fallback to default welcome message
        pass


# --------------------------
# Streamlit UI Components
# --------------------------
def display_chat_history():
    """
    Display the chat history in the Streamlit UI.
    This function handles the rendering of messages in the chat interface.
    """
    # Container for chat history with custom styling
    chat_container = st.container()
    
    with chat_container:
        # If no messages, show a fallback message
        if not st.session_state.conversation_history:
            with st.chat_message("assistant", avatar="🤖"):
                st.write("Hello! I'm SIA, your Support Intelligence Assistant. How can I help you today?")
            return
            
        # Display all messages in the conversation history
        for message in st.session_state.conversation_history:
            if message["role"] == "assistant":
                # Display assistant messages
                with st.chat_message("assistant", avatar="🤖"):
                    # Remove TERMINATE marker if present
                    clean_message = message["content"].replace(" TERMINATE", "")
                    st.write(clean_message)
            else:
                # Display user messages
                with st.chat_message("user", avatar="👤"):
                    st.write(message["content"])


def process_user_input(user_input):
    """
    Process user input and update the chat history.
    
    Args:
        user_input: The message input by the user
    """
    # Skip empty inputs
    if not user_input or user_input.strip() == "":
        return
        
    # Add user message to conversation history
    st.session_state.conversation_history.append({"role": "user", "content": user_input})
    
    if st.session_state.is_initialized and st.session_state.is_chat_active:
        with st.spinner("Processing..."):
            try:
                # Log the input being processed
                print(f"\nPROCESSING USER INPUT: '{user_input}'")
                
                # Send message to user agent
                user_agent = st.session_state.user_agent
                manager = st.session_state.manager
                
                # This is where the magic happens - we're using the AutoGen framework
                # to process the user's message and get a response
                reply = user_agent.send(
                    message=user_input,
                    recipient=manager,
                    request_reply=True
                )
                
                # Process the responses and update the chat history
                process_agent_responses()
                
            except Exception as e:
                error_msg = str(e)
                print(f"ERROR PROCESSING MESSAGE: {error_msg}")
                st.error(f"Error processing your message: {error_msg}")
                st.session_state.conversation_history.append(
                    {"role": "assistant", "content": f"I'm sorry, there was an error processing your request. Error: {error_msg}"}
                )


def process_agent_responses():
    """
    Process and update the chat history with agent responses.
    This function extracts new messages from the group chat and adds them to the conversation history.
    """
    # Get the conversation history from the group chat
    if hasattr(st.session_state.manager, 'groupchat'):
        groupchat = st.session_state.manager.groupchat
        messages = groupchat.messages
        
        # Debug log the messages
        print(f"\nCHAT MESSAGES (Total: {len(messages)})")
        for i, msg in enumerate(messages):
            sender = msg.get("name", "unknown")
            content = msg.get("content", "")
            content_preview = content[:50] + "..." if len(content) > 50 else content
            print(f"  MSG {i}: {sender} -> {content_preview}")
        
        # Find all SIA messages that haven't been added to our conversation history yet
        sia_messages = []
        for msg in messages:
            if msg.get("name") == "SIA" and "content" in msg:
                content = msg.get("content", "")
                
                # Skip function calls - only show human-readable responses
                if not content.startswith("FUNCTION_CALL:"):
                    sia_messages.append(content)
        
        # Get only messages that aren't already in the conversation history
        existing_assistant_messages = [m["content"] for m in st.session_state.conversation_history 
                                      if m["role"] == "assistant"]
        
        # Add new messages to the conversation history
        for content in sia_messages:
            if content not in existing_assistant_messages:
                print(f"ADDING NEW SIA RESPONSE: {content[:50]}...")
                st.session_state.conversation_history.append(
                    {"role": "assistant", "content": content}
                )


# --------------------------
# Main App Layout and Logic
# --------------------------
def main():
    """
    Main function that sets up and runs the Streamlit application.
    This function handles the overall layout and user interaction flow.
    """
    # Main app title and description
    st.title("🤖 Support Intelligence Assistant (SIA)")
    st.subheader("Get help with your listings and brand approvals")
    
    # Initialize chat if not already done
    if not st.session_state.is_initialized:
        with st.spinner("Initializing support chat..."):
            initialize_chat()
    
    # Start a new chat button
    if st.sidebar.button("Start New Chat", type="primary"):
        with st.spinner("Starting new conversation..."):
            initialize_chat()
            st.rerun()
    
    # Display current context in sidebar
    st.sidebar.subheader("Current Context")
    context = st.session_state.user_context
    st.sidebar.write(f"User ID: {context['user_id'] or 'Not provided'}")
    st.sidebar.write(f"Listing ID: {context['listing_id'] or 'Not provided'}")
    st.sidebar.write(f"Request ID: {context['request_id'] or 'Not provided'}")
    
    # Display chat status
    chat_status = "Active" if st.session_state.is_chat_active else "Ended"
    st.sidebar.metric("Chat Status", chat_status)
    
    # Sample input suggestions for testing
    st.sidebar.subheader("Quick Testing Inputs")
    col1, col2 = st.sidebar.columns(2)
    
    # Create a container for the testing buttons to help with the UI
    with st.sidebar.container():
        if col1.button("Listing Help", key="listing_help", use_container_width=True):
            process_user_input("I need help with my listing")
            st.rerun()
        if col2.button("Brand Approval", key="brand_approval", use_container_width=True):
            process_user_input("I need help with brand approval")
            st.rerun()
        
        # For topic selection in the conversation
        if col1.button("'listing'", key="listing_topic", use_container_width=True):
            process_user_input("listing")
            st.rerun()
        if col2.button("'brand approval'", key="brand_topic", use_container_width=True):
            process_user_input("brand approval")
            st.rerun()
            
        # For user IDs, create a row of buttons
        if col1.button("User ID: 12345", key="user_12345", use_container_width=True):
            process_user_input("12345")
            st.rerun()
        if col2.button("User ID: 56789", key="user_56789", use_container_width=True):
            process_user_input("56789")
            st.rerun()
            
        # For listing and request IDs
        if col1.button("Listing ID: 1234", key="listing_1234", use_container_width=True):
            process_user_input("1234")
            st.rerun()
        if col2.button("Request ID: 123", key="request_123", use_container_width=True):
            process_user_input("123")
            st.rerun()
    
    # Display conversation history
    display_chat_history()
    
    # Debug section for advanced debugging
    with st.sidebar.expander("Debug Info", expanded=False):
        if st.button("Show Full Message Chain", key="debug_messages"):
            st.write("Messages in groupchat:")
            if hasattr(st.session_state, 'manager') and hasattr(st.session_state.manager, 'groupchat'):
                for i, msg in enumerate(st.session_state.manager.groupchat.messages):
                    st.write(f"{i}: {msg.get('name')} -> {msg.get('content', '')[:70]}...")
    
    # User input at the bottom
    if st.session_state.is_chat_active:
        user_input = st.chat_input("Type your message here...")
        if user_input:
            process_user_input(user_input)
            st.rerun()
    else:
        st.info("This conversation has ended. Click 'Start New Chat' to begin a new conversation.")


# Ensure we always have the welcome message on first load
if __name__ == "__main__":
    # Initialize session state variables if they don't exist
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
        
    if 'user_context' not in st.session_state:
        st.session_state.user_context = {
            "user_id": None,
            "listing_id": None,
            "request_id": None
        }
        
    if 'is_initialized' not in st.session_state:
        st.session_state.is_initialized = False
        
    if 'is_chat_active' not in st.session_state:
        st.session_state.is_chat_active = True
        
    main() 