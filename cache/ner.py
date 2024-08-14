from ltp import LTP, StnSplit

def NER(text):
    # 初始化LTP模型
    ltp = LTP()
    
    # 使用StnSplit进行分句
    stn_split = StnSplit()
    sentences = stn_split.split(text)
    
    # 对整个文本进行处理
    result = ltp.pipeline(sentences, tasks=["cws", "pos", "ner"])
    
    # 提取所有命名实体，只保留实体名称
    entities = []
    for sentence_ner in result.ner:
        for entity in sentence_ner:
            _, entity_name, _, _ = entity
            entities.append(entity_name)
    
    print(">>>entities:", entities)
    return entities

# 使用示例
text = "王仁杰和邓怡翔去了萧山。"
result = NER(text)
print(result)