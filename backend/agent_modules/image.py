from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import os


dotenv_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path)

api_key=os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Function to create a file with the Files API
def create_file(file_path):
  with open(file_path, "rb") as file_content:
    result = client.files.create(
        file=file_content,
        purpose="vision",
    )
    return result.id

# Getting the file ID
file_id = create_file("/Users/dtvu/Downloads/cat copy.gif")

response = client.responses.create(
    model="gpt-4.1-mini",
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": "what's in this image?"},
            {
                "type": "input_image",
                "file_id": file_id,
            },
        ],
    }],
)

print(response.output)