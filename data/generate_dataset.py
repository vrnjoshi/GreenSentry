import json

# Expanded and corrected dataset
raw_data = [
    {
        "hungry": "while True: print('Checking updates...')",
        "green": "import time\nwhile True:\n    print('Checking updates...')\n    time.sleep(60)",
        "explanation": "Adding a sleep timer prevents 100% CPU usage during idle loops."
    },
    {
        "hungry": "data = [i for i in range(1000000)]\nfor x in data: print(x)",
        "green": "for x in range(1000000): print(x)",
        "explanation": "Using a generator/range instead of a full list saves significant RAM."
    },
    {
        "hungry": "import pandas as pd\ndf = pd.read_csv('huge_file.csv')",
        "green": "import pandas as pd\nfor chunk in pd.read_csv('huge_file.csv', chunksize=1000): process(chunk)",
        "explanation": "Processing data in chunks prevents memory spikes and disk swapping."
    },
    {
        "hungry": "requests.get('https://api.example.com/data') # called every second",
        "green": "# Setup a Webhook listener instead of polling\n@app.route('/webhook', methods=['POST'])\ndef handle_data(data): process(data)",
        "explanation": "Webhooks eliminate redundant network requests and server wake-ups."
    },
    {
        "hungry": "cursor.execute('SELECT * FROM global_users')",
        "green": "cursor.execute('SELECT username FROM global_users WHERE user_id = ?', (uid,))",
        "explanation": "Selecting only necessary columns reduces data transfer energy (Network Carbon)."
    },
    {
        "hungry": "for x in big_list:\n    result = heavy_computation(x)\n    process(result)",
        "green": "import functools\n@functools.lru_cache(maxsize=128)\ndef cached_heavy(x): return heavy_computation(x)\n\nfor x in big_list:\n    process(cached_heavy(x))",
        "explanation": "Caching/Memoization prevents the CPU from repeating expensive calculations."
    }
]

def create_jsonl(filename):
    with open(filename, 'w') as f:
        for entry in raw_data:
            structure = {
                "messages": [
                    {"role": "system", "content": "You are a Green Software SRE. Identify carbon-heavy code and provide a green refactor."},
                    {"role": "user", "content": f"Audit this code for energy efficiency: {entry['hungry']}"},
                    {"role": "assistant", "content": f"REFACTOR: {entry['green']}\nWHY: {entry['explanation']}"}
                ]
            }
            f.write(json.dumps(structure) + '\n')

if __name__ == "__main__":
    create_jsonl("data/fine_tuning_samples.jsonl")
    print("✅ Check /data/fine_tuning_samples.jsonl")