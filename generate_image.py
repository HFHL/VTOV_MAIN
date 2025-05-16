# 导入相关包

import sqlite3
import requests
import json
import time






# 分隔符
print("--------------------------------")

# 读取sqlite中的数据,提取一条记录的text字段,并返回text字段的长度和text字段本身.
# 输入: sqlite文件路径和id,id不是id字段而是行号
# 输出: text字段的长度和text字段本身
def read_sqlite_data(file_path, index):
    # 读取sqlite中的数据,提取一条记录的text字段,并返回text字段的长度和text字段本身.
    # 输入: sqlite文件路径和id
    # 输出: text字段的长度和text字段本身
    conn = sqlite3.connect(file_path)
    cursor = conn.cursor()
    # id不是id字段而是行号
    cursor.execute("SELECT text FROM wikipedia_zh_20231101 LIMIT 1 OFFSET ?", (index,))
    text_length = 0
    text = ""
    for row in cursor:
        text_length = len(row[0])
        text = row[0]
    conn.close()
    return text_length, text

# 调取api生成图片.
# 输入: text
# 输出：response结果
def generate_image(text, prompt):
    API_KEY = "b74589585d76d6641752b5711ca7f0bae40394471ba46f2d4e60134a91ece4d2"
    url = "https://api.wavespeed.ai/api/v3/wavespeed-ai/hidream-i1-full"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    payload = {
        "prompt": prompt,
        "size": "1024*1024",
        "seed": -1,
        "enable_base64_output": False,
        "enable_safety_checker": True
    }

    begin = time.time()
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        result = response.json()["data"]
        request_id = result["id"]
        print(f"Task submitted successfully. Request ID: {request_id}")
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return

    url = f"https://api.wavespeed.ai/api/v3/predictions/{request_id}/result"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    # Poll for results
    while True:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()["data"]
            status = result["status"]

            if status == "completed":
                end = time.time()
                print(f"Task completed in {end - begin} seconds.")
                url = result["outputs"][0]
                print(f"Task completed. URL: {url}")
                break
            elif status == "failed":
                print(f"Task failed: {result.get('error')}")
                break
            else:
                print(f"Task still processing. Status: {status}")
        else:
            print(f"Error: {response.status_code}, {response.text}")
            break

        time.sleep(0.1)

    return url

# main
if __name__ == "__main__":
    # text_length, text = read_sqlite_data("wikipedia_zh_20231101.sqlite", 1)
    # print(text_length)
    # print(text)

    text = "Anarchism is a political philosophy and movement that is skeptical of all justifications for authority and seeks to abolish the institutions it claims maintain unnecessary coercion and hierarchy, typically including nation-states, and capitalism."


    # original_prompt = "Front view.A realistic image of a white A4 paper with clear printed text in a standard font. The text should be neatly aligned and evenly spaced, resembling a document printed by a laser printer. The paper should be placed flat on a desk or surface, with no visible creases or distortions. The font should be legible and professional, as if it were a formal printed document.The string you need to print is as follows:"
    original_prompt = "Generate a picture of black text on white paper. The text content in the picture is as follows:"
    prompt = original_prompt + " " + text
    response_url = generate_image(text, prompt)
    # 将原始文本，生成的图片保存在本地。需要json来指定原始文本以及生成的图片的path。
    # 创建json文件，文件名称为text.json，文件内容为原始文本和生成的图片的path。
    json_data = {
        "text": text,
        "image_path": response_url
    }
    with open("text.json", "w") as f:
        json.dump(json_data, f)















