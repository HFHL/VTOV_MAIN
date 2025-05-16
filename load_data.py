from datasets import load_dataset

ds = load_dataset("wikimedia/wikipedia", "20231101.zh")

# 打印基本信息
print(ds)

# result：
# DatasetDict({
#     train: Dataset({
#         features: ['id', 'url', 'title', 'text'],
#         num_rows: 6407814
#     })
# })

# 打印前3行的text字段
print(ds["train"][:1]["text"])

# 打印分隔符
print("--------------------------------")

# 提取出['id', 'url', 'title', 'text'] 字段,保存在sqlite中. 自定义数据库结构.

import sqlite3

# 创建数据库
conn = sqlite3.connect("wikipedia_zh_20231101.sqlite")

# 创建游标
cursor = conn.cursor()

# 创建表
cursor.execute("CREATE TABLE wikipedia_zh_20231101 (id INTEGER, url TEXT, title TEXT, text TEXT)")

from tqdm import tqdm

# 插入数据,从ds中提取出前100条数据的['id', 'url', 'title', 'text'] 字段,保存在sqlite中.显示进度条.

for i in tqdm(range(100)):
    cursor.execute("INSERT INTO wikipedia_zh_20231101 (id, url, title, text) VALUES (?, ?, ?, ?)", (ds["train"][i]["id"], ds["train"][i]["url"], ds["train"][i]["title"], ds["train"][i]["text"]))

# 提交事务
conn.commit()

# 关闭连接
conn.close()

# 分隔符
print("--------------------------------")
print("数据已保存到sqlite中")




