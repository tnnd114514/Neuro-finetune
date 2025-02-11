import json

def convert_to_neuro_format(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    converted_data = []
    for item in data:
        converted_data.append({
            "context": [f"用户：{item['question']}"],
            "response": item['answer'],
            "metadata": {
                "emotion": {"sarcasm": 0.8, "humor": 0.7},
                "paralinguistic": ["*叹气*", "*摇头*"],
                "language_mix": {"en_ratio": 0.1, "jp_ratio": 0.05}
            }
        })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(converted_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    convert_to_neuro_format('data/raw_data.json', 'data/neuro_dataset.json')