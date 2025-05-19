import os
import json
import re
from tqdm import tqdm  # Для прогресс-бара (опционально)
def clean_text(content):
    # Удаляем ВСЁ до первого значимого заголовка текста (например, до "1. ")
    # Новый подход: удаляем всё до первого вхождения паттерна "\n\n1. " или другого маркера начала текста
    text_start = re.search(r'\n\s*\n\d+\.\s', content)  # Ищем "\n\n1. ", "\n\n2. " и т.д.
    if text_start:
        content = content[text_start.start():]
    
    # Удаляем конкретные навигационные элементы, если они остались
    nav_elements = [
        r'По разделам.*?Наши проекты',
        r'Зарегистрироваться.*?Наши проекты',
        r'Главная.*?Наши проекты',
        r'svyatye@dobroedelo\.ru'
    ]
    for pattern in nav_elements:
        content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # Удаляем "Телеграм канал" и всё после него
    end_marker = "Телеграм канал"
    end_pos = content.rfind(end_marker)
    if end_pos != -1:
        content = content[:end_pos]
    
    # Финальная очистка пустых строк
    content = re.sub(r'\n{3,}', '\n\n', content.strip())
    return content
def process_file(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    data['content'] = clean_text(data['content'])
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
def main():
    input_dir = 'svyatye-books'
    output_dir = 'svyatye-books-cleaned'
    
    os.makedirs(output_dir, exist_ok=True)
    
    files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
    print(f'Начата обработка {len(files)} файлов...')
    
    for filename in tqdm(files):
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        process_file(input_path, output_path)
    
    print('Готово! Очищенные файлы сохранены в:', output_dir)
if __name__ == '__main__':
    main()