def neuro_style_score(response):
    # 讽刺特征检测
    sarcasm_keywords = ["显然", "难道", "不是吗", "哈"]
    sarcasm_score = sum(response.count(word) for word in sarcasm_keywords) / len(response.split())
    
    # 幽默特征检测
    humor_keywords = ["搞笑", "滑稽", "玩笑", "幽默"]
    humor_score = sum(response.count(word) for word in humor_keywords) / len(response.split())
    
    # 句式复杂度
    sentence_length = sum(len(s.split()) for s in response.split('。')) / len(response.split('。'))
    
    return 0.5 * sarcasm_score + 0.3 * humor_score + 0.2 * min(sentence_length/15, 1)
