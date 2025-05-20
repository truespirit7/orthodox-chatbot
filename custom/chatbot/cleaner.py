import taskingai
import json  
import os  
import math  
from taskingai.retrieval import TokenTextSplitter  
import re
import time
from collections import defaultdict
from datetime import datetime

# Инициализация с вашим API ключом  
taskingai.init(api_key='tkUnNKlBXUJBNBq5A2YkNl0UxlTJ0yPR', host='http://localhost:8080')

# Глобальные настройки
MAX_COLLECTION_CAPACITY = 1000  # Максимальное количество записей в коллекции
MAX_RECORD_SIZE = 32000  # Максимальный размер одной записи
CHUNK_SIZE = 1000  # Размер чанков для текста
CHUNK_OVERLAP = 150  # Перекрытие чанков

# Словарь для статистики по коллекциям
collection_stats = defaultdict(int)

def filter_metadata(metadata):  
    """Фильтрует метаданные по ограничениям TaskingAI"""  
    filtered = {}  
    for key, value in metadata.items():  
        if len(filtered) >= 16:  
            break  
          
        key_str = str(key)  
        value_str = str(value)  
          
        if len(key_str) <= 64 and len(value_str) <= 512:  
            filtered[key_str] = value_str  
      
    return filtered

def create_new_collection(title=None, metadata=None):
    """Создает новую коллекцию с осмысленным именем"""
    # Формируем базовое имя коллекции
    if title:
        base_name = f"orthodox-{re.sub(r'[^a-zA-Zа-яА-Я0-9]', '-', title)[:40]}"
    else:
        base_name = "orthodox-texts"
    
    # Добавляем дату для уникальности
    date_str = datetime.now().strftime("%Y-%m-%d")
    collection_name = f"{base_name}-{date_str}"
    collection_name = collection_name[:64]  # Ограничение TaskingAI на длину имени
    
    # Формируем описание
    if title:
        description = f"Коллекция православных текстов: {title}"
    else:
        description = "Коллекция православных текстов"
    
    # Добавляем информацию из метаданных в описание, если есть
    if metadata:
        desc_additions = []
        if 'genre' in metadata:
            desc_additions.append(f"жанр: {metadata['genre']}")
        if 'year' in metadata:
            desc_additions.append(f"год: {metadata['year']}")
        if desc_additions:
            description += " (" + ", ".join(desc_additions) + ")"
    
    # Убедимся, что имя уникально
    suffix = 1
    original_name = collection_name
    while True:
        try:
            collections = taskingai.retrieval.list_collections()
            if collection_name not in [col.name for col in collections]:
                break
            collection_name = f"{original_name}-{suffix}"
            suffix += 1
        except Exception as e:
            print(f"Ошибка при проверке коллекций: {e}")
            time.sleep(5)
            continue
    
    try:
        collection = taskingai.retrieval.create_collection(  
            name=collection_name,  
            description=description,  
            embedding_model_id="TpINVr88",
            capacity=MAX_COLLECTION_CAPACITY
        )
        print(f"Создана новая коллекция: {collection.name} (ID: {collection.collection_id})")
        return collection
    except Exception as e:
        print(f"Ошибка при создании коллекции: {e}")
        time.sleep(5)
        return create_new_collection(title, metadata)  # Рекурсивный вызов с задержкой

def get_current_collection():
    """Получает текущую коллекцию или создает новую, если текущая заполнена"""
    try:
        collections = taskingai.retrieval.list_collections()
        if not collections:
            return create_new_collection()
        
        # Проверяем последнюю коллекцию
        last_collection = collections[-1]
        records = taskingai.retrieval.list_records(last_collection.collection_id)
        
        if len(records) >= MAX_COLLECTION_CAPACITY * 0.95:  # 95% заполнено
            return create_new_collection()
        return last_collection
    except Exception as e:
        print(f"Ошибка при проверке коллекций: {e}")
        time.sleep(5)
        return create_new_collection()

def process_book_file(file_path, current_collection=None):  
    """Обрабатывает один JSON-файл с книгой и загружает его в TaskingAI"""  
    filename = os.path.basename(file_path)  
      
    try:  
        # Читаем JSON файл  
        with open(file_path, 'r', encoding='utf-8') as file:  
            book_data = json.load(file)  
              
        # Извлекаем контент и метаданные  
        content = book_data.get("content", "")  
        metadata = book_data.get("metadata", {})  
        title = metadata.get("title", filename)  # Используем имя файла, если нет заголовка
          
        # Если коллекция не передана или заполнена, создаем новую
        if current_collection is None:
            current_collection = get_current_collection()
        
        # Проверяем заполненность текущей коллекции
        records = taskingai.retrieval.list_records(current_collection.collection_id)
        if len(records) >= MAX_COLLECTION_CAPACITY * 0.95:  # 95% заполнено
            current_collection = create_new_collection(title, metadata)
          
        # Разделяем контент на части  
        parts = split_content(content, title)  
        print(f"Контент в файле {filename} разделен на {len(parts)} частей")  
          
        # Загружаем каждую часть  
        for i, part_content in enumerate(parts):  
            # Проверяем заполненность коллекции перед каждой записью
            records = taskingai.retrieval.list_records(current_collection.collection_id)
            if len(records) >= MAX_COLLECTION_CAPACITY:
                current_collection = create_new_collection(f"{title}-продолжение", metadata)
              
            # Проверяем размер части  
            if len(part_content) > MAX_RECORD_SIZE:  
                print(f"ОШИБКА: Часть {i+1}/{len(parts)} файла {filename} превышает лимит ({len(part_content)} символов)")  
                continue  
                  
            # Создаем метаданные  
            part_metadata = metadata.copy()  
            part_metadata["part"] = str(i + 1)  
            part_metadata["total_parts"] = str(len(parts))  
            part_metadata["book_id"] = re.sub(r'[^a-zA-Zа-яА-Я0-9]', '_', title)[:50]  
            part_metadata["collection"] = current_collection.name
              
            # Фильтруем метаданные  
            filtered_metadata = filter_metadata(part_metadata)  
              
            try:
                time.sleep(1.0)  # Защита от rate limiting
  
                # Создаем запись  
                record = taskingai.retrieval.create_record(  
                    collection_id=current_collection.collection_id,  
                    type="text",  
                    content=part_content,  
                    title=f"{title} (Часть {i+1}/{len(parts)})",  
                    text_splitter=TokenTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP),  
                    metadata=filtered_metadata  
                )  

                # Обновляем статистику
                collection_stats[current_collection.name] += 1
                
                print(f"Успешно загружена часть {i+1}/{len(parts)} в коллекцию {current_collection.name}. Всего записей: {collection_stats[current_collection.name]}")
            except Exception as e:  
                print(f"Ошибка при загрузке части {i+1}/{len(parts)} файла {filename}: {str(e)}")  
                time.sleep(5)  # Увеличиваем задержку при ошибке
                  
        return current_collection  # Возвращаем текущую коллекцию для последующего использования
    except Exception as e:  
        print(f"Ошибка при обработке файла {filename}: {str(e)}")  
        return current_collection

def split_content(content, title):
    """Разделяет контент на части с учетом логической структуры и ограничений размера"""
    # Сначала пробуем разделить по логическим разделам
    logical_parts = split_by_logical_sections(content)
    
    # Проверяем, что все части соответствуют ограничениям
    valid_parts = []
    for part in logical_parts:
        if len(part) <= MAX_RECORD_SIZE:
            valid_parts.append(part)
        else:
            # Если часть слишком большая, делим ее на подчасти
            sub_parts = [part[i:i+MAX_RECORD_SIZE] for i in range(0, len(part), MAX_RECORD_SIZE)]
            valid_parts.extend(sub_parts)
    
    # Если логическое разделение не дало результатов, используем простое разделение
    if not valid_parts:
        valid_parts = [content[i:i+MAX_RECORD_SIZE] for i in range(0, len(content), MAX_RECORD_SIZE)]
    
    return valid_parts

def split_by_logical_sections(content):  
    """Разделяет текст по логическим разделам"""  
    section_markers = [  
        r"\n\s*Книга\s+\d+",
        r"\n\s*Часть\s+\d+",
        r"\n\s*Глава\s+\d+",   
        r"\n\s*Раздел\s+\d+",   
        r"\n\s*Предисловие",   
        r"\n\s*Послесловие",   
        r"\n\s*Введение",   
        r"\n\s*Глава\s+[IVXLCDM]+",  
        r"\n\s*§\s*\d+",  
        r"\n\s*\d+\.\s+",
        r"\n\s*[IVXLCDM]+\.\s+",  
        r"\n\s*\*\s*\*\s*\*",  
        r"\n\s*\-{3,}",  
        r"\n\s*[А-Я]{2,}[А-Я\s]+\n"  
    ]  
      
    pattern = '|'.join(section_markers)  
    matches = list(re.finditer(pattern, content))  
    if not matches:  
        return []  
      
    section_positions = [0] + [match.start() for match in matches] + [len(content)]  
    parts = [content[section_positions[i]:section_positions[i+1]] for i in range(len(section_positions)-1)]
      
    return parts

def main():
    book_dir = "svyatye-books-cleaned"
    book_files = [f for f in os.listdir(book_dir) if f.endswith(".json")]
    
    current_collection = None
    
    for book_file in book_files:
        file_path = os.path.join(book_dir, book_file)
        print(f"\nНачинаем обработку файла: {book_file}")
        
        current_collection = process_book_file(file_path, current_collection)
        
        # Выводим статистику по коллекциям
        print("\nТекущая статистика по коллекциям:")
        for col_name, count in collection_stats.items():
            print(f"- {col_name}: {count} записей")
        
        print(f"Файл {book_file} обработан. Текущая коллекция: {current_collection.name if current_collection else 'не определена'}")

if __name__ == "__main__":
    main()