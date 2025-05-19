import taskingai
import json  
import os  
import math  
from taskingai.retrieval import TokenTextSplitter  
import re
import time

  
# Инициализация с вашим API ключом  
taskingai.init(api_key='tkjRj062JOJVJ9b2jg5ihooXyU9LYqak', host='http://localhost:8080')  # или адрес вашего сервера
  
#Создание коллекции с моделью для эмбеддингов  
collection = taskingai.retrieval.create_collection(  
    name="orthodox-texts",  
    description="Коллекция творений святых отцов",  
    embedding_model_id="TpMmJhbV",  # ID модели эмбеддингов  
    capacity=1000  # Максимальное количество чанков  
)


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

def process_book_file(file_path, collection_id):  
    """Обрабатывает один JSON-файл с книгой и загружает его в TaskingAI"""  
    filename = os.path.basename(file_path)  
      
    try:  
        # Читаем JSON файл  
        with open(file_path, 'r', encoding='utf-8') as file:  
            book_data = json.load(file)  
              
        # Извлекаем контент и метаданные  
        content = book_data.get("content", "")  
        metadata = book_data.get("metadata", {})  
        title = metadata.get("title", "Без названия")  
          
        # Максимальный размер для одной части (с запасом)  
        MAX_SIZE = 32000  # Меньше лимита 32768 для безопасности  
          
        # Разделяем контент на части, гарантируя, что каждая часть меньше лимита  
        parts = []  
          
        # Сначала пробуем разделить по логическим разделам  
        logical_parts = split_by_logical_sections(content, MAX_SIZE)  
          
        # Проверяем, что все логические части меньше лимита  
        valid_logical_parts = True  
        for part in logical_parts:  
            if len(part) > MAX_SIZE:  
                valid_logical_parts = False  
                break  
          
        # Если логическое разделение не сработало, используем простое разделение  
        if not valid_logical_parts or not logical_parts:  
            print(f"Используем простое разделение для файла {filename}")  
            # Простое разделение по размеру  
            for i in range(0, len(content), MAX_SIZE):  
                parts.append(content[i:i+MAX_SIZE])  
        else:  
            parts = logical_parts  
              
        print(f"Контент в файле {filename} разделен на {len(parts)} частей")  
          
        # Загружаем каждую часть  
        for i, part_content in enumerate(parts):  
            # Проверяем размер части  
            if len(part_content) > MAX_SIZE:  
                print(f"ОШИБКА: Часть {i+1}/{len(parts)} файла {filename} превышает лимит ({len(part_content)} символов)")  
                continue  
                  
            # Создаем копию метаданных и добавляем информацию о части  
            part_metadata = metadata.copy()  
            part_metadata["part"] = str(i + 1)  
            part_metadata["total_parts"] = str(len(parts))  
            part_metadata["book_id"] = re.sub(r'[^a-zA-Zа-яА-Я0-9]', '_', title)[:50]  
              
            # Фильтруем метаданные  
            filtered_metadata = filter_metadata(part_metadata)  
              
            try:
                time.sleep(5.0)  
  
                # Создаем запись  
                record = taskingai.retrieval.create_record(  
                    collection_id=collection_id,  
                    type="text",  
                    content=part_content,  
                    title=f"{title} (Часть {i+1}/{len(parts)})",  
                    text_splitter=TokenTextSplitter(chunk_size=1000, chunk_overlap=150),  
                    metadata=filtered_metadata  
                )  

                print(f"Успешно загружена часть {i+1}/{len(parts)} файла: {filename}, record_id: {record.record_id}")  
            except Exception as e:  
                print(f"Ошибка при загрузке части {i+1}/{len(parts)} файла {filename}: {str(e)}")  
                  
        return True  
    except Exception as e:  
        print(f"Ошибка при обработке файла {filename}: {str(e)}")  
        return False  
  
def split_by_logical_sections(content, max_size):  
    """  
    Разделяет текст по логическим разделам, гарантируя, что каждая часть не превышает max_size  
    """  
    # Возможные маркеры разделов в православных текстах  
    section_markers = [  
        r"\n\s*Книга\s+\d+",
        r"\n\s*Часть\s+\d+",
        r"\n\s*Глава\s+\d+",   
        r"\n\s*Раздел\s+\d+",   
        r"\n\s*Предисловие*",   
        r"\n\s*Послесловие*",   
        r"\n\s*Введение*",   
        r"\n\s*Глава\s+[IVXLCDM]+",  # Римские цифры  
        r"\n\s*§\s*\d+",  
        r"\n\s*\d+\.\s+",  # Нумерованные разделы
        r"\n\s*[IVXLCDM]+\.\s+",  # Нумерованные разделы с римскими цифрами  
        r"\n\s*\*\s*\*\s*\*",  # Разделители  
        r"\n\s*\-{3,}",  # Горизонтальные линии  
        r"\n\s*[А-Я]{2,}[А-Я\s]+\n"  # ЗАГОЛОВКИ ПРОПИСНЫМИ  
    ]  
      
    # Объединяем все маркеры в один шаблон  
    import re  
    pattern = '|'.join(section_markers)  
      
    # Находим все разделы  
    matches = list(re.finditer(pattern, content))  
    if not matches:  
        # Если разделов не найдено, возвращаем пустой список,   
        # чтобы использовать простое разделение  
        return []  
      
    # Получаем позиции всех разделов  
    section_positions = [0] + [match.start() for match in matches] + [len(content)]  
      
    # Разделяем контент, гарантируя, что каждая часть не превышает max_size  
    parts = []  
    current_part = ""  
      
    for i in range(1, len(section_positions)):  
        section_start = section_positions[i-1]  
        section_end = section_positions[i]  
        section_text = content[section_start:section_end]  
          
        # Если секция сама по себе больше max_size, её нужно разделить дополнительно  
        if len(section_text) > max_size:  
            # Разделяем большую секцию на подчасти  
            for j in range(0, len(section_text), max_size):  
                parts.append(section_text[j:j+max_size])  
        else:  
            # Если добавление этой секции превысит лимит, начинаем новую часть  
            if len(current_part + section_text) > max_size:  
                if current_part:  
                    parts.append(current_part)  
                current_part = section_text  
            else:  
                current_part += section_text  
      
    # Добавляем последнюю часть, если она не пуста  
    if current_part:  
        parts.append(current_part)  
      
    return parts


book_dir = "svyatye-books-cleaned"
book_files = [f for f in os.listdir(book_dir) if f.endswith(".json")]
for book_file in book_files:
    file_path = os.path.join(book_dir, book_file)
    process_book_file(file_path, 'DbgYcaumykebvon2xup4d3fp')
    print(f"Обработан файл |||||||||||||||||||| {book_file}")

