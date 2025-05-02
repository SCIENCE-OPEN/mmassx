#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import csv
import xml.etree.ElementTree as ET
import tempfile
import re
import io
import xml.dom.minidom
import argparse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
from gui.libs import loadCompounds, compounds

GREEK_LETTERS = {
    'Α': 'alpha', 'Β': 'beta', 'Γ': 'gamma', 'Δ': 'delta', 'Ε': 'epsilon', 'Ζ': 'zeta',
    'Η': 'eta', 'Θ': 'theta', 'Ι': 'iota', 'Κ': 'kappa', 'Λ': 'lambda', 'Μ': 'mu',
    'Ν': 'nu', 'Ξ': 'xi', 'Ο': 'omicron', 'Π': 'pi', 'Ρ': 'rho', 'Σ': 'sigma',
    'Τ': 'tau', 'Υ': 'upsilon', 'Φ': 'phi', 'Χ': 'chi', 'Ψ': 'psi', 'Ω': 'omega',
    'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta', 'ε': 'epsilon', 'ζ': 'zeta',
    'η': 'eta', 'θ': 'theta', 'ι': 'iota', 'κ': 'kappa', 'λ': 'lambda', 'μ': 'mu',
    'ν': 'nu', 'ξ': 'xi', 'ο': 'omicron', 'π': 'pi', 'ρ': 'rho', 'σ': 'sigma',
    'τ': 'tau', 'υ': 'upsilon', 'φ': 'phi', 'χ': 'chi', 'ψ': 'psi', 'ω': 'omega'
}

SANITIZING_LOG_FILE = None  # will be set dynamically per file

def replace_greek_letters(text):
    return ''.join(GREEK_LETTERS.get(char, char) for char in text)

def log_error(message, row_id, row_data, sanitized_name=None, action_taken=None):
    try:
        name = row_data.get("name", "N/A")
        formula = row_data.get("chemical_formula", "N/A")
        if sanitized_name:
            message += f" | Name sanitized from '{name}' to '{sanitized_name}'"
        if action_taken:
            message += f" | Action taken: {action_taken}"
        with io.open(SANITIZING_LOG_FILE, "a", encoding="utf-8") as log_file:
            log_file.write(f"ERROR at row ID {row_id}: {message}\nName: {name}\nFormula: {formula}\n\n")
        print(f"Error detected at row ID {row_id}! {message} (Name: {name}, Formula: {formula})")
    except Exception as e:
        print(f"Logging failed for row {row_id}: {e}")

def sanitize_name(name, row_id=None, row_data=None):
    if not name:
        return ""
    if isinstance(name, bytes):
        name = name.decode("utf-8", errors="ignore")
    original_name = name
    name = name.replace("\u2010", "-").replace("±", "+/-").replace("¬", "").replace("→", " to ")
    name = re.sub(r"[†‡]+", "", name)

    substitutions = [
        ("5-(4’-hydroxyphenyl)-γ-valerolactone 4'-glucuronide", "C17H20O9"),
        ("5-(4’-hydroxyphenyl)-γ-valerolactone 4'-sulfate", "C11H12O6S"),
        ("2,2‚Äö√Ñ√∂?‚Äö√¢¬ß-(Hydroxynitrosohydrazino)bis-ethanamine", "C4H13N5O2"),
        ("O‐[(4Z)‐Decenoyl]carnitine", "O-[(4Z)-Decenoyl]carnitine")
    ]
    for pattern, replacement in substitutions:
        name = name.replace(pattern, replacement)

    regex_replacements = [
        (r".*rhamnoside.*", "Rhamnetin 3-rhamninoside"),
        (r".*Cyclo.*disulfide", "HMDB0250632"),
        (r".*Hydroxynitrosohydrazino.*", "HMDB0251069"),
        (r".*Bosutinib.*", "HMDB0240205"),
        (r".*hydroxylaurate.*", "12-Hydroxydodecanoate"),
        (r".*auriculatin.*", "HMDB0304570"),
        (r".*decadienoyl.*", "C31H50N7O17P3S")
    ]
    for pattern, replacement in regex_replacements:
        name = re.sub(pattern, replacement, name)

    name = replace_greek_letters(name)

    if original_name != name and row_id is not None and row_data is not None:
        log_error("Sanitized name", row_id, row_data, sanitized_name=name, action_taken="Replaced characters")

    return name

def create_temp_xml(compound_name, chemical_formula):
    temp_xml_path = os.path.join(tempfile.gettempdir(), "temp_compound.xml")
    root = ET.Element("mMassCompounds", version="1.0")
    group = ET.SubElement(root, "group", name="TemporaryGroup")
    ET.SubElement(group, "compound", name=compound_name, formula=chemical_formula)
    ET.ElementTree(root).write(temp_xml_path, encoding="utf-8", xml_declaration=True)
    return temp_xml_path

def loadCompoundsWrapper(path, expected_name=None):
    try:
        before_keys = set(compounds.get("TemporaryGroup", {}).keys())
        loadCompounds(path=path, clear=False)
        after_keys = set(compounds.get("TemporaryGroup", {}).keys())
        return expected_name in after_keys if expected_name else len(after_keys) > len(before_keys)
    except Exception as e:
        print(f"Failed to load with mMass: {e}")
        return False

def save_fixed_csv(csv_filename, rows, status=None):
    status_suffix = f"_{status}" if status else ""
    filename = os.path.splitext(os.path.basename(csv_filename))[0] + status_suffix + "_processed.csv"
    with open(filename, "w", encoding="utf-8", newline="") as csv_file:
        fieldnames = [f for f in rows[0].keys() if f != "UNKNOWN_FIELD"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            row.pop("UNKNOWN_FIELD", None)
            writer.writerow(row)
    print(f"Fixed CSV saved: {filename}")

def save_final_xml(csv_filename, compounds, status=None):
    status_suffix = f"_{status}" if status else ""
    filename = os.path.splitext(os.path.basename(csv_filename))[0] + status_suffix + "_processed.xml"
    root = ET.Element("mMassCompounds", version="1.0")
    group = ET.SubElement(root, "group", name="ProcessedGroup")
    for compound_name, chemical_formula in compounds:
        ET.SubElement(group, "compound", name=compound_name, formula=chemical_formula)
    ET.ElementTree(root).write(filename, encoding="utf-8", xml_declaration=True)
    print(f"Final XML saved: {filename}")

def process_csv_files(input_path):
    if os.path.isdir(input_path):
        csv_files = [os.path.join(root, f)
                     for root, _, files in os.walk(input_path)
                     for f in files if f.endswith(".csv") and not f.endswith("_processed.csv")]
    else:
        csv_files = [input_path] if input_path.endswith(".csv") else []

    if not csv_files:
        print(f"No CSV files found in '{input_path}'.")
        return

    for csv_file_path in csv_files:
        print(f"Processing file: {os.path.basename(csv_file_path)}...")

        global SANITIZING_LOG_FILE
        output_dir = os.path.dirname(csv_file_path)
        SANITIZING_LOG_FILE = os.path.join(output_dir, "sanitized_log.log")
        with open(SANITIZING_LOG_FILE, "w", encoding="utf-8") as f:
            pass

        fixed_rows_by_status = {}
        last_row = 1
        with open(csv_file_path, "r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            while True:
                try:
                    for row_id, row in enumerate(reader, start=last_row):
                        last_row = row_id + 1
                        row = {key.strip() if key else "UNKNOWN_FIELD": value for key, value in row.items()}
                        compound_name = row.get("name", "").strip()
                        chemical_formula = row.get("chemical_formula", "").strip()
                        if not compound_name or not chemical_formula:
                            continue
                        temp_xml_path = create_temp_xml(compound_name, chemical_formula)
                        if not loadCompoundsWrapper(temp_xml_path, compound_name):
                            sanitized_name = sanitize_name(compound_name, row_id, row)
                            temp_xml_path = create_temp_xml(sanitized_name, chemical_formula)
                            if not loadCompoundsWrapper(temp_xml_path, sanitized_name):
                                log_error("Failed to load compound even after sanitization", row_id, row, sanitized_name, action_taken="Still failed")
                                continue
                        status = row.get("status", "default").strip()
                        if status not in fixed_rows_by_status:
                            fixed_rows_by_status[status] = []
                        fixed_rows_by_status[status].append(row)
                    break
                except Exception as e:
                    print(f"Error on row {last_row}: {str(e)}. Skipping row and continuing.")
                    last_row += 1

        for status, rows in fixed_rows_by_status.items():
            valid_compounds = [(r["name"].strip(), r["chemical_formula"].strip()) for r in rows]
            save_final_xml(csv_file_path, valid_compounds, status)
            save_fixed_csv(csv_file_path, rows, status)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process and sanitize compound CSVs for mMass compatibility.")
    parser.add_argument("path", help="Path to CSV file or directory of CSVs")
    args = parser.parse_args()

    process_csv_files(args.path)
    print("Processing complete.")
