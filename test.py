import os
import time
from PIL import Image
from io import BytesIO
from google import genai
from google.genai import types

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

def generate_image(text, prompt, model_name):
    """
    调用API生成图片
    
    参数:
        text: 文本内容
        prompt: 提示词
        
    返回:
        成功时返回图片URL，失败时返回None
    """
    API_KEY = None
    client = genai.Client(api_key=API_KEY)
    begin = time.time()
    print(f"开始生成图片，文本长度: {len(text)}")
    image = None
    
    for i in range(5):
        if i > 0:
            print(f"重试第 {i+1} 次")
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
            if 'response' in locals():
                print(f"Full API response on error: {response}")
            time.sleep(1)
    return None

# generate_image("test", "test", "imagen")

text = "Nature 'is worth billions' to UK\nThe UK's parks, lakes, forests and wildlife are worth billions of pounds to the economy, says a major report.\nThe health benefits of merely living close to a green space are worth up to \u00a3300 per person per year, it concludes.\nThe National Ecosystem Assessment (NEA) says that for decades, the emphasis has been on producing more food and other goods - but this has harmed other parts of nature that generate hidden wealth.\nMinisters who commissioned the NEA will use it to re-shape planning policy.\n\"The natural world is vital to our existence, providing us with essentials such as food, water and clean air - but also cultural and health benefits not always fully appreciated because we get them for free,\" said Environment Secretary Caroline Spelman.\n\"The UK NEA is a vital step forward in our ability to understand the true value of nature and how to sustain the benefits it gives us.\"\nThe economic benefits of nature are seen most clearly in food production, which depends on organisms such as soil microbes, earthworms and pollinating insects.\nIf their health declines - as is currently happening in the UK with bees - either farmers produce less food, or have to spend more to produce the same amount.\nEither way there is an economic impact; and on average, the costs are growing over time.Degrading report\nEnd Quote Ian Bateman UEA\nWithout the environment, we're all dead - so the total value is infinite,\u201d\n\"Humans rely on the way ecosystems services control our climate - pollution, water quality, pollination - and we're finding out that many of these regulating services are degrading,\" said Bob Watson, chief scientific adviser to the Department for Environment, Food and Rural Affairs (Defra) and co-chairman of the NEA.\n\"About 30% of the key ecosystem services that we rely on are degrading.\n\"About 20% are getting better, however - our air quality has improved a lot - and what this report says is that we can do a lot better across the board,\" he told BBC News.\nThe 1940s saw the beginning of a national drive to increase production of food and other products such as timber.\nWhat are 'ecosystem services'?\n- The UN recognises four basic categories of ecosystem service that nature provides to humanity:\n- Provisioning - providing timber, wheat, fish, etc\n- Regulating - disposing of pollutants, regulating rainfall, storing carbon\n- Cultural - sacred sites, tourism, enjoyment of countryside\n- Supporting - maintaining soils and plant growth\nAlthough that was successful, the NEA finds there was a price to pay - England, for example, has the smallest percentage of forest cover anywhere in Europe, while many fish stocks are below optimum levels.\nThe report says the problem arises largely because currently, only material products such as food carry a pricetag in the market.\nBy calculating the value of less tangible factors such as clean air, clean water and natural flood defences, it hopes to rebalance the equation.\nThe Royal Society for the Protection of Birds (RSPB) welcomed the assessment.\n\"The traditional view of economic growth is based on chasing GDP, but in fact we will all end up richer and happier if we begin to take into account the true value of nature,\" said its conservation director, Martin Harper.\n\"Of course no-one can put a pounds and pence value on everything in nature - but equally we cannot ignore the importance of looking after it when we are striving for economic growth.\"\nThe NEA seeks to include virtually every economic contribution from eight types of landscape, such as woodlands, coasts and urban areas.\nIt also provides some local flavours by looking at variations across the UK.\nSome figures emerge with precision, such as the \u00a3430m that pollinating insects are calculated to be worth, or the \u00a31.5bn pricetag on inland wetlands, valued so high because they help to produce clean water.\nOther aspects of the evaluation are less precise because the costs and benefits are harder to quantify, and may change over time.World view\nIan Bateman, an economist from the University of East Anglia who played a principal role in the analysis, said that putting a single price on nature overall was not sensible.\n\"Without the environment, we're all dead - so the total value is infinite,\" he said.\n\"What is important is the value of changes - of feasible, policy-relevant changes - and those you can put numbers on.\"\nThe full 2,000-page report is stacked full of such numbers. The government intends to use some of them in its forthcoming Natural Environment White Paper and other initiatives that could reform urban and rural planning.\nProfessor Watson said this did not imply an end to development, but that costs and benefits of each proposed development could be assessed more accurately in advance.\n\"Urban green space, for example, is unbelievably important - if affects the value of houses, it affects our mental wellbeing.\n\"This report is saying 'this has got incredible value, so before you start converting green space into building, think through what the economic value is of maintaining that green space' - or the blue space, the ponds and the rivers.\"\nOn the global stage, several countries have previously evaluated the economic worth of specific factors such as forests or fisheries.\nAnd two international studies - the Millennium Ecosystem Assessment (MEA) and The Economics of Ecosystems and Biodiversity (Teeb) - have given broader views of society's environmental trajectory, and the costs and benefits.\nBut the UK is the first nation to produce such a detailed assessment across the piece."
variant_text = prepare_text(text, 400)
original_prompt = "Produce an image of a typed document page with the following text:"
prompt = original_prompt + " " + variant_text
image = generate_image(variant_text, prompt, "imagen")
        
dataset_dir="/Users/fchi/Code/toy/VTOV_MAIN/experiment_results_20250629_231810_imagen/bbc_5000/imagen_400"
# 定义文件路径 - 使用os.path.join确保路径正确
text_filepath = os.path.join(dataset_dir, "123890.txt")
image_filepath = os.path.join(dataset_dir, "123890.png")

# 保存文本
text_saved = save_text(variant_text, text_filepath)

# 保存图片
image_saved = save_image(image, image_filepath)
