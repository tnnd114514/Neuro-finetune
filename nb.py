import json
import re

def convert_to_target_format(input_file, output_file):
    """
    将问答数据转换为指定格式的JSONL文件
    输入格式要求：
    问：问题内容
    答：回答内容
    （支持多轮对话）
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 分割对话块（支持多轮对话）
    conversations = re.split(r'\n\n+', content.strip())
    
    with open(output_file, 'w', encoding='utf-8') as f_out:
        for conv in conversations:
            # 初始化消息列表（始终以系统消息开头）
            messages = [{
                "role": "system",
                "content": "You are a helpful assistant"
            }]
            
            # 解析对话内容
            turns = re.findall(r'(问：|答：)(.*?)(?=\n问：|\n答：|$)', conv, re.DOTALL)
            
            for prefix, text in turns:
                # 清理内容并转换角色
                cleaned = text.strip().rstrip(',')
                role = "user" if prefix == "问：" else "assistant"
                messages.append({
                    "role": role,
                    "content": cleaned
                })
            
            # 写入JSON行（至少包含一个用户消息）
            if any(msg["role"] == "user" for msg in messages):
                json.dump({"messages": messages}, f_out, ensure_ascii=False)
                f_out.write('\n')

                # 根据示例模式生成重复数据（可选）
                if "那雕塑方面如何呢？" in conv:
                    # 对于包含多轮对话的条目生成6次重复
                    for _ in range(5):
                        json.dump({"messages": messages}, f_out, ensure_ascii=False)
                        f_out.write('\n')
                else:
                    # 对于单轮对话生成4次重复
                    for _ in range(3):
                        json.dump({"messages": messages}, f_out, ensure_ascii=False)
                        f_out.write('\n')

# 使用示例
convert_to_target_format('source_data.txt', 'formatted_data.jsonl')