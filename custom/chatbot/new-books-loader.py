import taskingai
import json  
import os  
from taskingai.retrieval import TokenTextSplitter  
import re
import time
from datetime import datetime

# Инициализация API
taskingai.init(api_key='tkUnNKlBXUJBNBq5A2YkNl0UxlTJ0yPR', host='http://localhost:8080')

# Настройки
MAX_COLLECTION_CAPACITY = 1000
MAX_RECORD_SIZE = 32000
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
REQUEST_DELAY = 3.0  # Увеличенная задержка

# Текущая коллекция
current_collection_id = 'DbgYpk0nubrboqlwdlnb7nyj'

def create_new_collection():
    """Создает новую коллекцию с уникальным именем"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        collection_name = f"orthodox-{timestamp}"
        
        collection = taskingai.retrieval.create_collection(
            name=collection_name,
            description=f"Коллекция православных текстов (создана {timestamp})",
            embedding_model_id="TpINVr88",
            capacity=MAX_COLLECTION_CAPACITY
        )
        print(f"\nСоздана новая коллекция: {collection.collection_id}")
        return collection.collection_id
    except Exception as e:
        print(f"Ошибка создания коллекции: {e}")
        time.sleep(5)
        return create_new_collection()

def process_record(collection_id, content, title, metadata, part_num, total_parts):
    """Пытается создать запись, при ошибке RESOURCE_LIMIT_REACHED создает новую коллекцию"""
    global current_collection_id
    
    try:
        time.sleep(REQUEST_DELAY)
        
        record = taskingai.retrieval.create_record(
            collection_id=collection_id,
            type="text",
            content=content,
            title=f"{title} (Часть {part_num}/{total_parts})",
            text_splitter=TokenTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP),
            metadata=metadata
        )
        return True
    except Exception as e:
        if "RESOURCE_LIMIT_REACHED" in str(e):
            print(f"Коллекция заполнена, создаем новую...")
            current_collection_id = create_new_collection()
            return process_record(current_collection_id, content, title, metadata, part_num, total_parts)
        else:
            print(f"Ошибка загрузки части {part_num}: {str(e)}")
            time.sleep(5)
            return False

def process_book_file(file_path):
    """Обрабатывает файл книги"""
    global current_collection_id
    
    filename = os.path.basename(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            book_data = json.load(file)
        
        content = book_data.get("content", "")
        metadata = book_data.get("metadata", {})
        title = metadata.get("title", filename[:-5])  # Убираем .json
        
        # Разделение контента
        parts = []
        for i in range(0, len(content), MAX_RECORD_SIZE):
            parts.append(content[i:i+MAX_RECORD_SIZE])
        
        print(f"\nЗагрузка файла: {filename} ({len(parts)} частей)")
        
        # Загрузка частей
        for i, part in enumerate(parts, 1):
            part_metadata = metadata.copy()
            part_metadata.update({
                "part": str(i),
                "total_parts": str(len(parts)),
                "book_id": re.sub(r'[^a-zA-Z0-9]', '_', title)[:50]
            })
            
            success = process_record(
                current_collection_id,
                part,
                title,
                part_metadata,
                i,
                len(parts))
            
            if success:
                print(f"Часть {i}/{len(parts)} загружена в коллекцию {current_collection_id}")
            else:
                print(f"Не удалось загрузить часть {i}/{len(parts)}")
                
        return True
    except Exception as e:
        print(f"Ошибка обработки файла {filename}: {e}")
        return False

def main():
    book_dir = "svyatye-books-cleaned"
    book_files = [f for f in os.listdir(book_dir) if f.endswith(".json")]
    
    for book_file in book_files:
        file_path = os.path.join(book_dir, book_file)
        process_book_file(file_path)
        
        # Проверка заполненности текущей коллекции
        try:
            records = taskingai.retrieval.list_records(current_collection_id)
            print(f"\nТекущая коллекция {current_collection_id}: {len(records)}/{MAX_COLLECTION_CAPACITY} записей")
            if len(records) >= MAX_COLLECTION_CAPACITY * 0.9:  # 90% заполнено
                current_collection_id = create_new_collection()
        except Exception as e:
            print(f"Ошибка проверки коллекции: {e}")

if __name__ == "__main__":
    main()