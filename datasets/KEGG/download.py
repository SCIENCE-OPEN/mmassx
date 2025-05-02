import asyncio
import httpx
import csv
import os
import time
import random
from itertools import islice

BASE_URL = "https://rest.kegg.jp"
BATCH_SIZE = 10
MAX_CONCURRENT_REQUESTS = 1
MAX_RETRIES = 10
FAILED_BATCHES_FILE = "failed_batches.log"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
CACHE_DIR = "kegg_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_compound_list():
    list_url = f"{BASE_URL}/list/compound"
    response = httpx.get(list_url, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return [line.split("\t")[0] for line in response.text.strip().split("\n")]

def get_existing_data(output_file):
    if not os.path.exists(output_file):
        return set()
    existing_ids = set()
    with open(output_file, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader, None)
        for row in reader:
            if row:
                existing_ids.add(row[0])
    return existing_ids

def chunked_iterable(iterable, size):
    it = iter(iterable)
    while chunk := list(islice(it, size)):
        yield chunk

async def fetch_batch(client, batch):
    compound_ids = "+".join(batch)
    cache_file = os.path.join(CACHE_DIR, f"{compound_ids}.txt")

    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()

    compound_url = f"{BASE_URL}/get/{compound_ids}"

    for attempt in range(MAX_RETRIES):
        try:
            response = await client.get(compound_url, timeout=20, headers={"User-Agent": USER_AGENT})
            if response.status_code == 200:
                with open(cache_file, "w", encoding="utf-8") as f:
                    f.write(response.text)
                return response.text
            print(f"Failed ({response.status_code}) for batch {compound_ids}, retrying...")

            retry_delay = (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(retry_delay)
        except httpx.RequestError as e:
            print(f"Error fetching {compound_ids}: {e}")
            retry_delay = (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(retry_delay)

    print(f"Skipping batch {compound_ids} after {MAX_RETRIES} attempts.")
    with open(FAILED_BATCHES_FILE, "a") as f:
        f.write(compound_ids + "\n")
    return None

async def download_missing_compounds(output_file="kegg_metabolites.csv", map_output_file="kegg_metabolites_maps.csv"):
    all_compounds = get_compound_list()
    existing_ids = get_existing_data(output_file)
    missing_ids = [comp_id for comp_id in all_compounds if comp_id not in existing_ids]

    if not missing_ids:
        print("No missing compounds found.")
        return

    print(f"Found {len(missing_ids)} missing compounds. Downloading in batches...")

    async with httpx.AsyncClient() as client:
        tasks = set()
        results = []
        start_time = time.time()

        for batch in chunked_iterable(missing_ids, BATCH_SIZE):
            if len(tasks) >= MAX_CONCURRENT_REQUESTS:
                done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                results.extend([task.result() for task in done if task.result()])

            tasks.add(asyncio.create_task(fetch_batch(client, batch)))

        results.extend(await asyncio.gather(*tasks))

    compound_data, compound_name_dynamic_data, compound_map_dynamic_data = parse_responses(results)
    save_to_csv(output_file, compound_data, compound_name_dynamic_data, compound_map_dynamic_data)
    save_map_to_csv(map_output_file, compound_map_dynamic_data)

    elapsed_time = time.time() - start_time
    print(f"Download complete in {elapsed_time:.2f} seconds.")

def parse_responses(responses):
    compound_data = []
    compound_name_dynamic_data = []
    compound_map_dynamic_data = []

    for response in responses:
        if not response:
            continue

        compounds = response.strip().split("///")
        for compound in compounds:
            lines = [line for line in compound.strip().split("\n") if line.strip()]
            if not lines or len(lines[0].split()) < 2:
                continue

            compound_id = lines[0].split()[1]
            names, maps = [], []
            formula = ""
            current_key = ""

            for line in lines:
                if line.startswith("NAME"):
                    current_key = "NAME"
                    names.append(line.replace("NAME", "").strip().rstrip(";"))
                elif line.startswith("PATHWAY"):
                    current_key = "PATHWAY"
                    maps.append(line.split()[1])
                elif line.startswith("FORMULA"):
                    formula = line.replace("FORMULA", "").strip()
                elif current_key == "NAME" and line.startswith(" "):
                    names.append(line.strip().rstrip(";"))
                elif current_key == "PATHWAY" and line.startswith(" "):
                    maps.append(line.split()[0])
                else:
                    current_key = ""

            compound_data.append([compound_id, formula])
            compound_name_dynamic_data.append(names)
            compound_map_dynamic_data.append(maps)

    return compound_data, compound_name_dynamic_data, compound_map_dynamic_data

def save_to_csv(output_file, compound_data, compound_name_dynamic_data, compound_map_dynamic_data):
    # Sort all entries by KEGG_ID (compound_data[i][0])
    combined = list(zip(compound_data, compound_name_dynamic_data, compound_map_dynamic_data))
    combined.sort(key=lambda x: x[0][0])  # Sort by KEGG_ID string

    # Unpack sorted data
    compound_data, compound_name_dynamic_data, compound_map_dynamic_data = zip(*combined)
    compound_data = list(compound_data)
    compound_name_dynamic_data = list(compound_name_dynamic_data)
    compound_map_dynamic_data = list(compound_map_dynamic_data)

    # Build headers
    name_cols = max(map(len, compound_name_dynamic_data), default=0)
    map_cols = max(map(len, compound_map_dynamic_data), default=0)
    headers = ["KEGG_ID", "chemical_formula"] + \
              [f"name_{i+1}" for i in range(name_cols)] + \
              [f"map_{i+1}" for i in range(map_cols)]

    # Write CSV
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        for i, row in enumerate(compound_data):
            names = compound_name_dynamic_data[i]
            maps = compound_map_dynamic_data[i]
            writer.writerow(row + names + maps)

def save_map_to_csv(map_output_file, compound_map_dynamic_data):
    with open(map_output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Map name", "Compounds"])
        map_dict = {}
        for i, maps in enumerate(compound_map_dynamic_data):
            for map_name in maps:
                if map_name not in map_dict:
                    map_dict[map_name] = []
                map_dict[map_name].append(f"C{i+1}")
        for map_name, compounds in map_dict.items():
            writer.writerow([map_name, ";".join(compounds)])

if __name__ == "__main__":
    asyncio.run(download_missing_compounds())
