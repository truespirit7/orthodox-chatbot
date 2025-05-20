import taskingai  
from taskingai.assistant import Assistant
from taskingai.assistant.memory import AssistantMemory

# Инициализация клиента TaskingAI  
taskingai.init(api_key='tkUnNKlBXUJBNBq5A2YkNl0UxlTJ0yPR', host='http://localhost:8080')  
  
# Инициализация клиента TaskingAI  
  
# Получение списка всех коллекций с дополнительной информацией  
collections = taskingai.retrieval.list_collections(limit=100)  
# collections = taskingai.collection.list_ui_collections(limit=105)  
  
# Извлечение ID и имен моделей эмбеддингов для всех коллекций  
  
print(f"Найдено {len(collections)} коллекций:")  
# Список ID коллекций, которые нужно добавить в ассистента  
collection_ids = [collection.collection_id for collection in collections]  

# Создание списка ссылок на коллекции  
retrievals_test = [{"type": "collection", "id": collection_id} for collection_id in collection_ids]  
  # Создание объекта памяти  

# Создание ассистента с несколькими коллекциями 
assistant = taskingai.assistant.create_assistant(
    model_id="TpyrJnla",
    name="My Assistant",
    description="Православный ассистент",
    system_prompt_template=["Ты православный чат-бот. Отвечай на вопросы пользователя в соответствии с текстами православных святых отцов. Эти тексты соответствую запросу пользователя, используй их для правильного и точного ответа на его вопрос:"],
    # memory=AssistantMemory(type="message_window", max_tokens=1000),
    memory=AssistantMemory(),
    tools=[],
    retrievals=retrievals_test,
    retrieval_configs={  
        "method": "function_call",  # или "user_message"  
        "top_k": 5,  
        "score_threshold": 0.7  
    }
)
# assistant: Assistant = taskingai.assistant.create_assistant(
#     model_id="$$MODEL_ID$$",
#     name="My Assistant",
#     description="This is my assistant",
#     system_prompt_template=["You are a professional assistant speaking {{language}}."],
#     memory=AssistantMemory(),
#     tools=[],
#     retrievals=[],
# )

# assistant = taskingai.assistant.create_assistant(  
#     model_id="TpyrJnla",  
#     memory={"type": "message_window"},  
#     name="Ассистент с несколькими коллекциями",  
#     description="Ассистент с доступом к нескольким коллекциям знаний",  
#     retrievals=retrievals,  
#     retrieval_configs={  
#         "method": "function_call",  # или "user_message"  
#         "top_k": 5,  
#         "score_threshold": 0.7  
#     }  
# )  
  
print(f"Создан ассистент с ID: {assistant.assistant_id}")  
print(f"Добавлены коллекции: {collection_ids}")