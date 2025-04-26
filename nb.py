import json
import re

def convert_to_jsonl(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 分割问答对（处理可能存在的空行）
    qa_pairs = re.split(r'\n\n+', content.strip())
    
    with open(output_file, 'w', encoding='utf-8') as f_out:
        for pair in qa_pairs:
            # 提取所有问答轮次（支持多轮对话）
            messages = [
                {
                    "role": "system", 
                    "content": "You are a famous AI virtual anchor Neuro-sama."
                }
            ]
            
            # 分割问答轮次
            rounds = re.findall(r'(问：|答：)(.*?)(?=\n问：|\n答：|$)', pair, re.DOTALL)
            
            for prefix, text in rounds:
                role = "user" if prefix == "问：" else "assistant"
                # 清理内容：去除首尾空白和结尾的逗号
                cleaned = text.strip().rstrip(',')
                messages.append({
                    "role": role,
                    "content": cleaned
                })
            
            # 写入JSON行
            if len(messages) > 1:  # 至少包含一个有效问答
                json.dump({"messages": messages}, f_out, ensure_ascii=False)
                f_out.write('\n')

# 使用示例
convert_to_jsonl('yyyy.txt', 'converted_training_data.txt')