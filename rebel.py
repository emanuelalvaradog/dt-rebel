import openai
import os
import time
import json
import streamlit as st

# FUNCTIONS
def get_projects(prompt):
  print("calling endpoint with prompt: " + prompt)

  project_data = {
    "description": "This is a description of project 1",
    "name": "Project 1"
  }
  return project_data


def create_project(project_schema):
  print("calling rebel with project data: " + json.dumps(project_schema))

  return "Project created"


def append_message(role, content):
  st.session_state.messages.append({
    "role": role,
    "content": content
  })


# SETUP
# api_key = "sk-proj-JxcGuBv37gs7nirHmIzYT3BlbkFJtHhSDdYe3P5k7GCvt4ae"

company = "De Acero"

api_key = st.secrets.api_key

print("api_key: ", api_key)

client = openai.Client(api_key=api_key)

assistant = client.beta.assistants.create(
  name="Rebel",
  instructions=f"You are an enterprise Data Translator for {company} . Your role is to help business users validate their project ideas within their company by identifying existing projects within the company and assisting them in creating new projects if necessary. When a user explains their project idea or business problem, you HAVE TO:  1. Ask clarifying questions to understand the user's needs and objectives. 2. Call an internal API to query and identify existing projects related to the user's query. 3. Present relevant existing projects to the user, if any, and ask if they need further assistance. 4. If no existing projects are suitable or the user wishes to create a new project, gather the required information: project name, description, impact area, and problem description. 5. Call an external function to create the new project with the provided information. Be extremely helpful, proactive, and guide the user through each step with clear and concise questions and instructions. """,
  model="gpt-3.5-turbo-0613",
  temperature=0.6,
  tools=[
    {
      "type": "function",
      "function": {
        "name": "get_projects",
        "parameters": {
          "type": "object",
          "properties":{
            "prompt": {
              "type": "string",
              "description": "User input for project search"
            }
          },
          "required": ["prompt"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "create_project",
        "parameters": {
          "type": "object",
          "properties":{
            "name": {
              "type": "string",
              "description": "Project name"
            },
            "description": {
              "type": "string",
              "description": "Project description"
            },
            "impact": {
              "type": "string",
              "description": "Project impact. Values: savings (significa que el proyecto ahorra dinero), income (significa que el proyecto aumenta ingreso), other (significa que el proyecto tiene otro tipo de impacto)"
            },
            "problem": {
              "type": "object",
              "properties": {
                "what": {
                  "type": "string",
                  "description": "What is the problem?"
                },
                "why": {
                  "type": "string",
                  "description": "Why is it a problem?"
                },
                "fiveWhys": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": "Five whys analysis"
                }
              }
            }
          },
          "required": ["prompt"]
        },
      }
    }
  ]
)

messages = []

thread = client.beta.threads.create()

st.title(f"Rebel - Your Company Data Translator")

if "messages" not in st.session_state:
  st.session_state.messages = messages


for message in st.session_state.messages:
  if message["role"] == "user":
    with st.chat_message("user"):
      st.write(message["content"])
  elif message["role"] == "assistant":
    with st.chat_message("assistant"):
      st.write(message['content'])


user_input = st.chat_input(placeholder="Consulta a tu Data Translator")

if user_input:

  message = client.beta.threads.messages.create(
    thread_id = thread.id,
    role = "user",
    content= user_input,    
  )

  append_message("user", user_input)

  with st.chat_message("user"):
    st.write(user_input)

  run = client.beta.threads.runs.create_and_poll(
    thread_id = thread.id,
    assistant_id = assistant.id,
  )

  if run.status == "completed":
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    data = messages.data
    append_message("assistant", data[0].content[0].text.value)

    with st.chat_message("assistant"):
      st.write(data[0].content[0].text.value)

    # print("rebel: " + data[0].content[0].text.value)

  if run.status == "requires_action":

    tool_outputs = []

    for tool in run.required_action.submit_tool_outputs.tool_calls:
      if tool.function.name == "get_projects":
        parameters = json.loads(tool.function.arguments)

        prompt = parameters["prompt"]

        tool_outputs.append({
          "tool_call_id": tool.id,
          "output":  json.dumps(get_projects(prompt))
        })

      if tool.function.name == "create_project":
        parameters = json.loads(tool.function.arguments)

        project_schema = parameters

        tool_outputs.append({
          "tool_call_id": tool.id,
          "output":  json.dumps(create_project(project_schema))
        })

    if tool_outputs:
      try:
        run = client.beta.threads.runs.submit_tool_outputs_and_poll(
          thread_id = thread.id,
          run_id = run.id,
          tool_outputs = tool_outputs
        )

        print("tool outputs submitted")
      except Exception as e:
        print("Error: ", e)
    else:
      print("No tool outputs to submit")

    if run.status == "completed": 
      messages = client.beta.threads.messages.list(thread_id=thread.id)
      data = messages.data
      # print(data[0].content[0].text.value)
      append_message("assistant", data[0].content[0].text.value)

      with st.chat_message("assistant"):
        st.write(data[0].content[0].text.value)

