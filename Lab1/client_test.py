from openai import OpenAI

# Configure client to point to local Ollama instance
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # Required by SDK format; ignored by Ollama
)

message_history=[
    {"role":"system",
    "content":"You are an academic mentor."
    }
]
def run_chat_loop():
    print("Chat started. Type 'exit' or 'quit' to stop.")

    while True:
        user_input = input("You: ")
        if user_input.strip().lower() in ['exit', 'quit']:
            print("Exiting chat")
            break
            
        message_history.append({"role": "user", "content": user_input})
        
        response = client.chat.completions.create(
            model="qwen2.5:1.5b",
            temperature=0.2,
            messages=message_history
        )
        
        print(f"\nModel Output: {response.choices[0].message.content}\n")
        
        message_history.append({"role": "assistant", "content": response.choices[0].message.content})

if __name__ == "__main__":
    run_chat_loop()