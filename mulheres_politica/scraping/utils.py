import json
import csv
from pathlib import Path


def save_to_json(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✓  Dados salvos em: {filepath}")


def save_to_csv(data, filepath, fieldnames=None):
    if not data:
        print("  ✗ Sem dados para salvar!")
        return
    
    if fieldnames is None:
        fieldnames = list(data[0].keys())
    
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"  ✓  Dados salvos em: {filepath}")


def clean_text(text):
    if not text:
        return ""
    return text.strip()