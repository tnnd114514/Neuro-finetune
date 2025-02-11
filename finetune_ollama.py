from ollama import Client
from datasets import load_from_disk
import json

# 初始化Ollama客户端
client = Client(host='http://localhost:11434')

# 加载数据
# 修改数据加载部分
dataset = load_from_disk('data/processed/processed_dataset')

# 微调配置
with open('configs/training_args.json') as f:
    train_args = json.load(f)

# 准备微调数据
train_data = [
    {"input": item['input'], "output": item['output']}
    for item in dataset
]

# 开始微调
response = client.create_model(
    name="neuro-style-model",
    base="deepseek-r1-distill-llama-70b",
    train_data=train_data,
    parameters={
        "lora_rank": train_args['lora_rank'],
        "learning_rate": train_args['learning_rate'],
        "num_epochs": train_args['num_train_epochs'],
        "batch_size": train_args['per_device_train_batch_size']
    }
)

print("微调完成，模型保存为：", response['model'])