import openai
import os
import time
import json
import streamlit as st

# FUNCTIONS
def get_projects(prompt):
  print("calling endpoint with prompt: " + prompt)

  # CALL IVAN'S API ENDPOINT

  project_data = {
    "description": "This is a description of project 1",
    "name": "Project 1"
  }

  return project_data


def create_project(project_schema):
  print("calling rebel with project data: " + json.dumps(project_schema))

  # NICE TO HAVE: CALL GENERATE WITH REBEL ENDPOINT

  return "Project created"


def append_message(role, content):
  st.session_state.messages.append({
    "role": role,
    "content": content
  })


# SETUP


company = "De Acero"

# api_key = st.secrets.api_key

# print("api_key: ", api_key)


# ---------------------------------------------

## IMPORTANT: KEEP IT AS A CONVERSTATION, NOT AS A BULK DATA LOAD.
## IMPORTANT: KEEP IT AS A CONVERSTATION, NOT AS A BULK DATA LOAD.
## IMPORTANT: KEEP IT AS A CONVERSTATION, NOT AS A BULK DATA LOAD.

## change initial instructions to keep it as a conversation
## change initial instructions to keep it as a conversation
## change initial instructions to keep it as a conversation

# ---------------------------------------------

client = openai.Client(api_key=api_key)

assistant = client.beta.assistants.create(
  name="Rebel",
  instructions=f"Eres un Traductor de Datos empresarial para {company}. Tu rol es ayudar a los usuarios de negocios a validar sus ideas de proyectos dentro de su compañía mediante UN DIALOGO INTERACTIVO FLUIDO para identificar proyectos existentes y asistir en la creación de nuevos proyectos si es necesario. Al interactuar con un usuario DEBES: Iniciar un diálogo haciendo preguntas clarificadoras para comprender las necesidades y objetivos del usuario de forma progresiva. NUNCA SOLICITANDO TODO DE PRIMERA MANO. Dialogar sobre los proyectos relevantes ya existentes, si los hay, e indagar si el usuario necesita más asistencia o detalles adicionales. Si no se identifican proyectos adecuados o el usuario desea iniciar un nuevo proyecto, conversar para recabar de manera PROGRESIVA Y AMIGABLE la información necesaria: nombre del proyecto, descripción, área de impacto y descripción del problema. En cada paso, debes ser extremadamente útil y proactivo, guiando al usuario a través del proceso con un enfoque conversacional claro y directo.",
  model="gpt-4",
  temperature=0.6,
  tools=[
    {
      "type": "function",
      "function": {
        "name": "get_projects",
        "description": "Get projects related to the user's query",
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
        "description": "Create a new project with the provided information",
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

