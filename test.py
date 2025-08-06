from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import json
from PIL import Image
from IPython.display import display, Markdown
load_dotenv()

# Initialize the Gemini client with the API key from environment variables
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)
MODEL_ID = "gemini-2.5-flash"  # Specify the model ID you want to use


prompt = """
    What are the best ways to sort a list of n numbers from 0 to m?
    Generate and run Python code for three different sort algorithms.
    Provide the final comparison between algorithm clearly.
    Is one of them linear?
"""

thinking_budget = 4096 # @param {type:"slider", min:0, max:24576, step:1}

code_execution_tool = types.Tool(
    code_execution=types.ToolCodeExecution()
    
)

response = client.models.generate_content(
    model=MODEL_ID,
    contents=prompt,
    config=types.GenerateContentConfig(
        tools=[code_execution_tool],
        thinking_config=types.ThinkingConfig(
            thinking_budget=thinking_budget,
        )
    ),
)

from IPython.display import HTML, Markdown

for part in response.candidates[0].content.parts:
  print(dir(part))
  if part.text is not None:
    print(f"**{part.text}**")
    display(Markdown(part.text))
  if part.executable_code is not None:
    print(f"**Executing code:** {part.executable_code.code}")
    code_html = f'<pre style="background-color: green;">{part.executable_code.code}</pre>' # Change code color
    display(HTML(code_html))
  if part.code_execution_result is not None:
    print(f"**Code execution result:** {part.code_execution_result.output}")
    display(Markdown(part.code_execution_result.output))
display(Markdown("---"))