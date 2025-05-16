import sqlite3
import requests
import json
import time
import os
import shutil
from urllib.request import urlretrieve
import random

# 设置读取SQLite记录的数量
NUM_RECORDS_TO_PROCESS = 1  # 可以修改这个数字来控制处理的记录数量

# 创建保存文件的目录
def create_directories():
    os.makedirs("text", exist_ok=True)
    os.makedirs("image", exist_ok=True)
    print("已创建text和image目录")

# 读取sqlite中的数据
def read_sqlite_data(file_path, limit=None):
    """
    从SQLite数据库中读取数据
    
    参数:
        file_path: SQLite数据库文件路径
        limit: 限制读取的记录数，None表示读取所有记录
        
    返回:
        包含rowid和text的记录列表
    """
    conn = sqlite3.connect(file_path)
    cursor = conn.cursor()
    
    if limit:
        cursor.execute("SELECT rowid, text FROM wikipedia_en_20231101 LIMIT ?", (limit,))
    else:
        cursor.execute("SELECT rowid, text FROM wikipedia_en_20231101")
    
    records = []
    for row in cursor:
        records.append({"rowid": row[0], "text": row[1]})
    
    conn.close()
    print(f"从数据库读取了 {len(records)} 条记录")
    return records

# 生成截取不同长度的文本
def generate_text_variants(text, lengths=[20, 50, 80]):
    """
    从原始文本中截取指定长度的文本片段
    
    参数:
        text: 原始文本
        lengths: 需要截取的长度列表
        
    返回:
        包含不同长度文本的字典
    """
    variants = {}
    for length in lengths:
        if len(text) >= length:
            variants[length] = text[:length]
        else:
            # 如果原始文本长度不足，则使用全部文本
            variants[length] = text
    return variants

# 调用API生成图片
def generate_image(text, prompt):
    """
    调用API生成图片
    
    参数:
        text: 文本内容
        prompt: 提示词
        
    返回:
        成功时返回图片URL，失败时返回None
    """
    API_KEY = "b74589585d76d6641752b5711ca7f0bae40394471ba46f2d4e60134a91ece4d2"
    url = "https://api.wavespeed.ai/api/v3/wavespeed-ai/hidream-i1-full"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    payload = {
        "prompt": prompt,
        "size": "1024*1024",
        "seed": random.randint(1, 10000),  # 使用随机种子
        "enable_base64_output": False,
        "enable_safety_checker": True
    }

    begin = time.time()
    print(f"开始生成图片，文本长度: {len(text)}")
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            result = response.json()["data"]
            request_id = result["id"]
            print(f"任务提交成功。请求ID: {request_id}")
        else:
            print(f"错误: {response.status_code}, {response.text}")
            return None

        url = f"https://api.wavespeed.ai/api/v3/predictions/{request_id}/result"
        headers = {"Authorization": f"Bearer {API_KEY}"}

        # 轮询获取结果
        while True:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                result = response.json()["data"]
                status = result["status"]

                if status == "completed":
                    end = time.time()
                    print(f"任务完成，耗时 {end - begin:.2f} 秒")
                    image_url = result["outputs"][0]
                    print(f"图片URL: {image_url}")
                    return image_url
                elif status == "failed":
                    print(f"任务失败: {result.get('error')}")
                    return None
                else:
                    print(f"任务处理中. 状态: {status}")
            else:
                print(f"错误: {response.status_code}, {response.text}")
                return None

            time.sleep(2)  # 每2秒检查一次状态
    except Exception as e:
        print(f"生成图片时发生错误: {str(e)}")
        return None

# 保存图片到本地
def save_image(url, filepath):
    """
    将图片URL保存到本地文件
    
    参数:
        url: 图片URL
        filepath: 本地保存路径
        
    返回:
        成功返回True，失败返回False
    """
    try:
        urlretrieve(url, filepath)
        print(f"图片已保存至: {filepath}")
        return True
    except Exception as e:
        print(f"保存图片失败: {str(e)}")
        return False

# 保存文本到本地
def save_text(text, filepath):
    """
    将文本保存到本地文件
    
    参数:
        text: 文本内容
        filepath: 本地保存路径
        
    返回:
        成功返回True，失败返回False
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"文本已保存至: {filepath}")
        return True
    except Exception as e:
        print(f"保存文本失败: {str(e)}")
        return False

# 主函数
def main(sqlite_path, limit=5):
    # 创建目录
    create_directories()
    
    # 读取数据库
    records = read_sqlite_data(sqlite_path, limit)
    
    # 基础提示词
    original_prompt = "Generate a picture of black text on white paper. The text content in the picture is as follows:"
    
    # 记录所有生成结果
    generation_log = []
    
    # 处理每条记录
    for record in records:
        rowid = record["rowid"]
        text = record["text"]
        
        # 生成不同长度的文本变体
        text_variants = generate_text_variants(text)
        
        # 对每个长度的文本变体生成图片
        for length, variant_text in text_variants.items():
            
            prompt = original_prompt + " " + variant_text
            
            # 记录本次生成的信息
            generation_info = {
                "rowid": rowid,
                "text_length": length,
                "text": variant_text,
                "prompt": prompt,
                "status": "pending"
            }
            
            # 调用API生成图片
            image_url = generate_image(variant_text, prompt)
            
            if image_url:
                # 定义文件路径
                text_filepath = f"text/{rowid}_len{length}.txt"
                image_filepath = f"image/{rowid}_len{length}.png"
                
                # 保存文本
                text_saved = save_text(variant_text, text_filepath)
                
                # 保存图片
                image_saved = save_image(image_url, image_filepath)
                
                # 更新生成信息
                generation_info.update({
                    "image_url": image_url,
                    "local_text_path": text_filepath,
                    "local_image_path": image_filepath,
                    "status": "success" if (text_saved and image_saved) else "partial_success"
                })
            else:
                generation_info["status"] = "failed"
            
            # 添加到日志
            generation_log.append(generation_info)
            
            # 记录当前进度到临时文件
            with open("generation_log_temp.json", "w", encoding="utf-8") as f:
                json.dump(generation_log, f, ensure_ascii=False, indent=2)
            
            # 休息一下，避免API请求过快
            time.sleep(1)
    
    # 记录所有生成结果到JSON文件
    with open("generation_log.json", "w", encoding="utf-8") as f:
        json.dump(generation_log, f, ensure_ascii=False, indent=2)
    
    print(f"所有任务完成，共处理了 {len(generation_log)} 个文本片段")
    print(f"生成日志已保存到 generation_log.json")

if __name__ == "__main__":
    # SQLite数据库文件路径
    sqlite_path = "/Users/apple/code/vtov/VTOV_MAIN/wikipedia_en_20231101.sqlite"
    
    # 从数据库中读取指定数量的记录进行测试
    main(sqlite_path, limit=NUM_RECORDS_TO_PROCESS)