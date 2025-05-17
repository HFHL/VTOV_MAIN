import sqlite3
import requests
import json
import time
import os
import shutil
from urllib.request import urlretrieve
import random
import argparse
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

# 设置读取SQLite记录的数量
NUM_RECORDS_TO_PROCESS = 5  # 可以修改这个数字来控制处理的记录数量

# 创建保存文件的目录
def create_directory(dataset_dir="dataset"):
    # 创建主目录，使用os.path.join确保路径兼容性
    os.makedirs(dataset_dir, exist_ok=True)
    print(f"Created directory: {dataset_dir}")

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
    # conn = sqlite3.connect(file_path)
    # cursor = conn.cursor()
    
    # if limit:
    #     cursor.execute("SELECT rowid, text FROM wikipedia_en_20231101 LIMIT ?", (limit,))
    # else:
    #     cursor.execute("SELECT rowid, text FROM wikipedia_en_20231101")
    
    # records = []
    # for row in cursor:
    #     records.append({"rowid": row[0], "text": row[1]})
    
    # conn.close()
    # print(f"从数据库读取了 {len(records)} 条记录")
    with open("dataset_gt5000chars_20records.json", "r", encoding="utf-8") as f:
        records = json.load(f)
    records = records[:limit]
    return records

# 生成截取不同长度的文本
def prepare_text(text, length=1000):
    """
    从原始文本中截取指定长度的文本片段，确保不会截断单词
    
    参数:
        text: 原始文本
        length: 需要截取的长度，默认为1000
        
    返回:
        截取后的文本，不会在单词中间截断
    """
    if len(text) >= length:
        # Find the last space before the specified length to avoid cutting words
        truncated_text = text[:length]
        last_space_index = truncated_text.rfind(' ')
        
        # If a space was found, truncate at that position
        if last_space_index != -1:
            return text[:last_space_index]
        else:
            # If no space was found (rare case with very long words), return as is
            return truncated_text
    else:
        # 如果原始文本长度不足，则使用全部文本
        print(f"Warning: Text length {len(text)} is less than requested length {length}")
        return text

# 调用API生成图片
def generate_image(text, prompt, model_name):
    """
    调用API生成图片
    
    参数:
        text: 文本内容
        prompt: 提示词
        
    返回:
        成功时返回图片URL，失败时返回None
    """
    API_KEY = "AIzaSyDAlR5-Y8tZslkLJQjOCwC_kV-m9-kaeSs"
    client = genai.Client(api_key=API_KEY)
    begin = time.time()
    print(f"开始生成图片，文本长度: {len(text)}")
    image = None
    
    try:
        if model_name == "imagen":
            response = client.models.generate_images(
                model='imagen-3.0-generate-002',
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    include_rai_reason=True,
                    output_mime_type='image/jpeg',
                )
            )
            image = Image.open(BytesIO(response.generated_images[0].image.image_bytes))

        elif model_name == "gemini":
            response = client.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE', 'TEXT']
                )
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image = Image.open(BytesIO(part.inline_data.data))
                    # image.show()
                    break
            
        end = time.time()
        print(f"任务完成，耗时 {end - begin:.2f} 秒")
        return image
    except Exception as err:
        print(f"任务失败: {str(err)}")
        return None

def save_image(image, filepath):
    """
    将图片保存到本地文件
    
    参数:
        image: PIL Image对象
        filepath: 本地保存路径
        
    返回:
        成功返回True，失败返回False
    """
    if image is None:
        return False
    try:
        image.save(filepath)
        print(f"图片已保存至: {filepath}")
        return True
    except Exception as e:
        print(f"保存图片失败: {str(e)}")
        return False

# 保存图片到本地
def save_image_url(url, filepath):
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
def main(sqlite_path, limit=5, model_name="imagen", prompt_id=0, text_length=1000, dataset_dir="dataset"):
    # 使用传入的text_length参数
    
    # 创建目录
    create_directory(dataset_dir)
    
    # 读取数据库
    records = read_sqlite_data(sqlite_path, limit)
    
    # 定义不同的提示词
    prompts = [
        "Generate a scanned document image with following text:",
        "Create a mockup of a scanned document containing the text:",
        "Design a sample document scan with the following text:",
        "Generate an image of printed note that include this text:",
        "Produce an image of a typed document page with the following text:",
        "Generate a document scan visualization showing this text:",
        "Produce a sample of how a scanned memo might look with this text:",
        "Generate an image of a plain Word document with black text on white background without decorative elements, document should contain this text:"
    ]
    
    # 选择提示词
    if 0 <= prompt_id < len(prompts):
        original_prompt = prompts[prompt_id]
    else:
        print(f"Warning: Invalid prompt_id {prompt_id}, using default prompt")
        original_prompt = prompts[0]
    
    # 记录所有生成结果
    generation_log = []
    
    # 处理每条记录
    for record in records:
        rowid = record["rowid"]
        text = record["text"]
        
        # 处理文本
        variant_text = prepare_text(text, text_length)
            
        prompt = original_prompt + " " + variant_text
        
        # 记录本次生成的信息
        generation_info = {
            "rowid": rowid,
            "text_length": text_length,
            "text": variant_text,
            "prompt": prompt,
            "status": "pending"
        }
            
        # 调用API生成图片
        image = generate_image(variant_text, prompt, model_name)
        
        if image:
            # 定义文件路径 - 使用os.path.join确保路径正确
            text_filepath = os.path.join(dataset_dir, f"{rowid}.txt")
            image_filepath = os.path.join(dataset_dir, f"{rowid}.png")
                
            # 保存文本
            text_saved = save_text(variant_text, text_filepath)
            
            # 保存图片
            image_saved = save_image(image, image_filepath)
            
            # 更新生成信息
            generation_info.update({
                "local_text_path": text_filepath,
                "local_image_path": image_filepath,
                "status": "success" if (text_saved and image_saved) else "partial_success"
            })
        else:
            generation_info["status"] = "failed"
        
        # 添加到日志
        generation_log.append(generation_info)
        
        # 记录当前进度到临时文件（放在dataset_dir目录内）
        log_temp_path = os.path.join(dataset_dir, "generation_log_temp.json")
        with open(log_temp_path, "w", encoding="utf-8") as f:
            json.dump(generation_log, f, ensure_ascii=False, indent=2)
        
        # 休息一下，避免API请求过快
        time.sleep(1)
    
    # 记录所有生成结果到JSON文件（保存在dataset_dir目录内）
    log_path = os.path.join(dataset_dir, "generation_log.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(generation_log, f, ensure_ascii=False, indent=2)
    
    print(f"All tasks completed. Processed {len(generation_log)} text segments.")
    print(f"Generation log saved to {log_path}")

if __name__ == "__main__":

    # 创建参数解析器
    parser = argparse.ArgumentParser(description="Generate images from text using different models and prompts")
    
    # 添加命令行参数
    parser.add_argument("--model", type=str, default="imagen", choices=["imagen", "gemini"],
                        help="Model to use for image generation")
    parser.add_argument("--content_length", type=int, default=1000,
                        help="Content length to process")
    parser.add_argument("--prompt_id", type=int, default=0,
                        help="ID of the prompt template to use (0, 1, or 2)")
    parser.add_argument("--limit", type=int, default=NUM_RECORDS_TO_PROCESS,
                        help="Number of records to process from the database")
    parser.add_argument("--sqlite_path", type=str, default="wikipedia_en_20231101.sqlite",
                        help="Path to the SQLite database file")
    parser.add_argument("--dataset_dir", type=str, default="dataset",
                        help="Directory to store the generated dataset")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 从数据库中读取指定数量的记录进行测试
    main(
        sqlite_path=args.sqlite_path,
        limit=args.limit,
        model_name=args.model,
        prompt_id=args.prompt_id,
        text_length=args.content_length,
        dataset_dir=args.dataset_dir
    )
