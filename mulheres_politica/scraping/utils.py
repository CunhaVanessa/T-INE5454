"""
Utility functions for web scraping operations.

This module provides common utility functions used across different
scraping modules for data processing and file operations.
"""

import json
import csv
from pathlib import Path


def save_to_json(data, filepath):
    """
    Save data to a JSON file.
    
    Args:
        data: Data to be saved (list or dict).
        filepath: Path where the JSON file will be saved.
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Data saved to {filepath}")


def save_to_csv(data, filepath, fieldnames=None):
    """
    Save data to a CSV file.
    
    Args:
        data: List of dictionaries to be saved.
        filepath: Path where the CSV file will be saved.
        fieldnames: List of field names for CSV header. If None, will use keys from first item.
    """
    if not data:
        print("No data to save")
        return
    
    if fieldnames is None:
        fieldnames = list(data[0].keys())
    
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"Data saved to {filepath}")


def load_from_json(filepath):
    """
    Load data from a JSON file.
    
    Args:
        filepath: Path to the JSON file.
        
    Returns:
        Loaded data from JSON file.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def clean_text(text):
    """
    Clean and normalize text data.
    
    Args:
        text: Text string to be cleaned.
        
    Returns:
        str: Cleaned text.
    """
    if not text:
        return ""
    return text.strip()
