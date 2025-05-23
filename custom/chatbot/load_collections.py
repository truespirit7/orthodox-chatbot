import taskingai  
from taskingai.assistant import Assistant
from taskingai.assistant.memory import AssistantMemory

taskingai.init(api_key='tkjRj062JOJVJ9b2jg5ihooXyU9LYqak', host='http://localhost:8080')  

# Получить существующего ассистента  
assistant = taskingai.assistant.get_assistant(assistant_id="X5lMjyPs7GA9AaoiE0fpTUvU")  
  
# Получить все коллекции  
collections = taskingai.retrieval.list_collections()  
# Создать список retrievals для всех коллекций  
new_retrievals = []  

for collection in collections:    
    new_retrievals.append({  
        "type": "collection",  
        "id": collection.collection_id  
    })
# Обновить ассистента с новыми коллекциями  
updated_assistant = taskingai.assistant.update_assistant(  
    assistant_id=assistant.assistant_id,  
    retrievals=new_retrievals,  
    retrieval_configs={  
        "top_k": 3,  
        "max_tokens": 1000,  
        "score_threshold": 0.5,  
        "method": "user_message"  
    }  
)