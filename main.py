import json
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
import argparse
from prompts import system_prompt
from call_function import available_functions, call_function
from config import MAX_ITERATIONS

PROTECTED_FILES = {"calculator.py"}  # the decoy/root file — NOT pkg/calculator.py

def main():

    parser = argparse.ArgumentParser(description="Chatbot")
    parser.add_argument("user_prompt", type=str, help="User Prompt")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    user_prompt = args.user_prompt

    load_dotenv()
    api_key = os.getenv("OPEN_ROUTER_API_KEY")
    if api_key is None:
        raise ValueError("OPEN_ROUTER_API_KEY is not set in the environment variables.")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )

    messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    for i in range(MAX_ITERATIONS):
        
        response = client.chat.completions.create(
            model = "openrouter/free",
            messages = messages,
            temperature = 0,
            tools = available_functions,
    )
        
        message = response.choices[0].message
        messages.append(message)
                
        if args.verbose:
            print(f"User prompt: {user_prompt}")
            print(f"Prompt tokens: {response.usage.prompt_tokens}")
            print(f"Response tokens: {response.usage.completion_tokens}")
        
        
        if message.tool_calls:
            for tool_call in message.tool_calls:
                result_message = call_function(tool_call, verbose=args.verbose)

            if not result_message["content"]:
                raise Exception(f"Fatal error: function call for {tool_call.function.name} returned no content")

            if args.verbose:
                print(f"-> {result_message['content']}")
                
                messages.append(result_message)
        else:
                    print(f"Response:\n{message.content}")
                    return
    print(f"Max iterations ({MAX_ITERATIONS}) reached without final response")
    sys.exit(1)    
    



if __name__ == "__main__":
    main()
