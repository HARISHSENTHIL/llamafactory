# import datasets
# import json

# dataset_name = "sebdg/supply_chain_q_a"
# subset_size = 1339

# dataset = datasets.load_dataset(dataset_name)

# small_dataset = dataset['train'].shuffle(seed=42).select(range(subset_size))

# formatted_data = [
#     {
#         "instruction": entry["instruction"], 
#         "input": entry.get("input", ""),      
#         "output": entry["output"]             
#     }
#     for entry in small_dataset
# ]

# with open("supply-chain.json", "w") as json_file:
#     json.dump(formatted_data, json_file, indent=2)

# print("Reduced dataset saved successfully in the desired JSON format!")




# import datasets
# import json

# dataset_name = "StaAhmed/Football_Question_Answers"
# subset_size = 3000


# dataset = datasets.load_dataset(dataset_name)

# small_dataset = dataset['train'].shuffle(seed=42).select(range(subset_size))
# # small_dataset = dataset['train'].select(range(subset_size))

# formatted_data = [entry for entry in small_dataset]

# with open("football-info.json", "w") as json_file:
#     json.dump(formatted_data, json_file, indent=2)

# print("Reduced dataset saved successfully as JSON!")


import json
from datasets import load_dataset

def convert_to_alpaca_format(input_data):
    alpaca_formatted_data = []

    for entry in input_data:
        alpaca_entry = {
            "input": entry["question"],
            "output": entry["answer"]
        }
        alpaca_formatted_data.append(alpaca_entry)

    return alpaca_formatted_data
input_data = load_dataset("AmjadKha/BankingDataset", split='train').select(range(2000))

# input_data = load_dataset("AmjadKha/BankingDataset", split='train').shuffle(seed=42).select(range(2000))
converted_data = convert_to_alpaca_format(input_data)

with open('Banking-info.json', 'w') as f:
    json.dump(converted_data, f, indent=4)

print("Conversion completed and saved to 'supply-chain-alpaca.json'")
