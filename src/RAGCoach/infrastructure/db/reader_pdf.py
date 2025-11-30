import pdfplumber
import json
import os
from pathlib import Path

def pdf_to_json(pdf_file, json_file):
    try:
        print(f"Открываем {pdf_file}...")
        
        with pdfplumber.open(pdf_file) as pdf:
            result = {}
            
            for i, page in enumerate(pdf.pages):
                print(f"Обрабатывается страница {i+1}...")
                text = page.extract_text()
                
                if text and text.strip():
                    result[f"page_{i+1}"] = text
                else:
                    result[f"page_{i+1}"] = "Текст не найден"
            
            # Сохраняем в JSON
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Успех! JSON сохранен в {json_file}")
            return True
            
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return False

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parents[3]    

    DATA_DIR = BASE_DIR / "data/"

    pdf_filename = DATA_DIR + "Лекция 01.pdf"
    json_filename = DATA_DIR + "output.json"
    
    if os.path.exists(pdf_filename):
        pdf_to_json(pdf_filename, json_filename)
    else:
        print(f"Файл {pdf_filename} не найден!")
        print("Положите PDF файл в ту же папку, что и этот скрипт")
    
    input("Нажмите Enter...")