import json
from datasets import Dataset
from pathlib import Path

def preprocess_data(input_file, output_dir):
    # 读取原始数据
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 转换格式
    processed = []
    for item in data:
        processed.append({
            'input': f"用户：{item['question']}",
            'output': item['answer'],
            'metadata': {
                'emotion': {'sarcasm': 0.8, 'humor': 0.7},
                'paralinguistic': ["*叹气*", "*摇头*"],
                'language_mix': {'en_ratio': 0.1, 'jp_ratio': 0.05}
            }
        })
    
    # 保存处理后的数据
    dataset = Dataset.from_list(processed)
    dataset.save_to_disk(str(Path(output_dir) / 'processed_dataset'))

if __name__ == "__main__":
    preprocess_data(
        input_file='data/raw/your_file.json',
        output_dir='data/processed'
    )
