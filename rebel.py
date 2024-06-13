import openai
import os
import time
import json
import streamlit as st
from setup import SingletonAssistant
import requests

# FUNCTIONS
def get_projects(prompt):
  print("calling endpoint with prompt: " + prompt)

  results = requests.post(url="https://rag-service-eg5yxvopfa-uc.a.run.app/query", json={"prompt": prompt})

  documents = results.json()

  documents = json.dumps(documents["documents"])

  return documents


def create_project(project_schema):
  print("calling rebel with project data: " + json.dumps(project_schema))

  # NICE TO HAVE: CALL GENERATE WITH REBEL ENDPOINT

  return "Project created"


def append_message(role, content):
  st.session_state.messages.append({
    "role": role,
    "content": content
  })


messages = []

if "messages" not in st.session_state:
  st.session_state.messages = messages

# SETUP
api_key = st.secrets.api_key

client, assistant, thread = SingletonAssistant.get_instance(api_key=api_key)

st.title(f"Rebel - Your Company Data Translator")

for message  in st.session_state.messages:
  if message["role"] == "user":
    with st.chat_message("user"):
      st.write(message["content"])
      
  elif message["role"] == "assistant":
    with st.chat_message("assistant"):
      st.write(message["content"])

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
          "output":  get_projects(prompt)
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

      append_message("assistant", data[0].content[0].text.value)

      # print(data[0].content[0].text.value)

      with st.chat_message("assistant"):
        st.write(data[0].content[0].text.value)

