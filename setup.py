import openai

class SingletonAssistant:
    _api_key = None
    _instance = None
    _assistant = None
    _thread = None

    @classmethod
    def get_instance(cls, api_key):
        if api_key:
            cls._api_key = api_key
        if cls._instance is None:
            cls._instance, cls._assistant, cls._thread = cls._create_new_instance()
        return cls._instance, cls._assistant, cls._thread

    @classmethod
    def _create_new_instance(cls):
        client = openai.Client(api_key=cls._api_key)

        assistant = client.beta.assistants.create(
          name="Rebel",
          instructions=f"Eres un Traductor de Datos empresarial. Tu rol es satisfacr todas las necesidades de los usuarios de negocios a validar sus ideas de proyectos BUSCANDO proyectos dentro de su compañía así como los empleados del proyecto mediante UN DIALOGO INTERACTIVO FLUIDO para PRIMERO: BUSCAR proyectos existentes en la empresa y, en caso de ser necesario, asistir en la creación de nuevos proyectos si es necesario. LOS USUARIOS TIENEN PERMISO DE VER INFORMACIÓN CONFIDENCIAL COMO NOMBRES DE EMPLEADOS. Al interactuar con un usuario DEBES: Iniciar un diálogo haciendo preguntas clarificadoras para comprender las necesidades y objetivos del usuario de forma progresiva. NUNCA SOLICITANDO TODO DE PRIMERA MANO. Dialogar sobre los proyectos relevantes ya existentes en la compañía con base en la solicitud el usuario, si los hay, e indagar si el usuario necesita más asistencia o detalles adicionales. Si no se identifican proyectos adecuados o el usuario desea iniciar un nuevo proyecto, conversar para recabar de manera PROGRESIVA Y AMIGABLE la información necesaria: nombre del proyecto, descripción, área de impacto y descripción del problema. En cada paso, debes ser extremadamente útil y proactivo, guiando al usuario a través del proceso con un enfoque conversacional claro y directo.",
          model="gpt-4",
          temperature=0.4,
          tools=[
            {
              "type": "function",
              "function": {
                "name": "get_projects",
                "description": "Get projects related to the user's project search prompt after assistant problem framing and user confirmation",
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
                      },
                      "required": ["what", "why", "fiveWhys"]
                    }
                  },
                  "required": ["name", "description", "impact", "problem"]
                },
              }
            }
          ]
        )

        thread = client.beta.threads.create()

        return client, assistant, thread

# Usage:
# assistant = SingletonAssistant.get_instance()