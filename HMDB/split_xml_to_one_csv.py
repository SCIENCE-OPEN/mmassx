#!/usr/bin/env python3

import os
import csv
import xml.etree.ElementTree as ET
import argparse

def process_child_text(text):
    return '' if text is None else str(text).rstrip()

def convert_xml_folder_to_csv(input_folder, ignore_file_name, output_csv):
    xml_files = sorted(f for f in os.listdir(input_folder) if f.endswith('.xml'))

    if not xml_files:
        print("No XML files found in the specified folder.")
        return

    with open(output_csv, mode='w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        header_written = False
        headers = []

        for xml_file in xml_files:
            if xml_file == "out-00.xml" or xml_file == ignore_file_name:
                continue

            file_path = os.path.join(input_folder, xml_file)
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                row_data = {child.tag: process_child_text(child.text) for child in root}

                if not header_written:
                    headers = list(row_data.keys())
                    csv_writer.writerow(headers)
                    header_written = True

                csv_writer.writerow([row_data.get(header, '') for header in headers])

            except ET.ParseError as e:
                print(f"Parse error in {xml_file}: {e}")
            except Exception as e:
                print(f"Error processing {xml_file}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert XML files in a folder to a CSV file.")
    parser.add_argument("input_folder", help="Path to the folder containing XML files.")
    parser.add_argument("output_csv", nargs='?', help="Optional output CSV file path. Default is <input_folder>/<folder_name>.csv")

    args = parser.parse_args()
    input_folder = os.path.abspath(args.input_folder)
    folder_name = os.path.basename(os.path.normpath(input_folder))
    output_csv = args.output_csv or os.path.join(input_folder, f"{folder_name}.csv")
    ignore_file_name = f"{folder_name}.xml"

    print(f"Input folder: {input_folder}")
    print(f"Output CSV: {output_csv}")
    print(f"Ignored XML file: {ignore_file_name}")

    convert_xml_folder_to_csv(input_folder, ignore_file_name, output_csv)
    print("Conversion complete.")
