import requests
import PyPDF2
import io
import json
import os
from datetime import datetime
import re

# --- 配置区 ---
# 请注意：直接在代码中嵌入API密钥存在安全风险。
# 建议使用环境变量或其他安全方式管理您的API密钥。
API_KEY = 'AIzaSyDy9pYAEW7e2Ewk__9TCHAD5X_G1VhCtVw' # 您提供的API Key
# 您提供的模型名称。如果此模型不可用，您可能需要替换为公开可用的模型，例如 'gemini-1.5-flash-latest'
MODEL_NAME = 'gemini-2.0-flash-exp'
GEMINI_API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}'

# --- 辅助函数 ---

def download_pdf(pdf_url):
    """下载PDF文件并返回其二进制内容"""
    print(f"正在从 {pdf_url} 下载PDF...")
    try:
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()  # 如果请求失败则抛出HTTPError
        print("PDF下载成功！")
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"下载PDF失败: {e}")
        return None

def extract_text_from_pdf(pdf_content):
    """从PDF的二进制内容中提取文本"""
    print("正在提取PDF文本...")
    text = ""
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() or "" # 添加 "or """ 以处理NoneType
        print(f"PDF文本提取完成，共提取约 {len(text)} 字符。")
        if not text.strip():
            print("警告：提取到的文本为空。PDF可能是图片格式或者内容无法识别。")
        return text
    except Exception as e:
        print(f"提取PDF文本失败: {e}")
        return None

def generate_xiaohongshu_post(paper_text):
    """调用Gemini API生成小红书风格的论文解读"""
    print("正在调用Gemini API生成科普文章...")

    # 对于 arxiv.py，我们使用完整的 paper_text，不再截断
    # REMOVED: truncated_paper_text = paper_text[:20000]

    # 为Gemini API精心设计的Prompt (使用完整文本，并移除摘要提示)
    # 用户已将字数调整为800-900
    prompt = f"""作为一位资深的科技内容创作者和分析师，你的任务是根据以下科研论文的文本，撰写一篇既专业准确又不失趣味性的科普解读文章，目标读者是对科技有一定兴趣的普通大众。文章字数在800-900中文字符左右。

请遵循以下指导方针：

1.  **文章标题**：在解读内容的第一行，使用 `标题：` 标记。标题应精炼、引人注目，并能准确反映论文的核心贡献或最有趣的发现。例如："AI新突破：机器视觉首次实现X功能"或"深度解析：Y理论如何颠覆我们对Z的认知"。

2.  **开篇**：用简洁的几句话点明研究的背景、试图解决的关键问题及其潜在的重要性或新奇之处，以吸引读者继续阅读。

3.  **核心内容解读**：
    *   **研究动机与背景**：清晰阐述这项研究为何被提出，它针对的是什么现状或挑战。
    *   **方法与技术亮点**：用准确且易于理解的语言解释论文采用的关键方法和技术。如果涉及复杂概念，尝试用简明的方式解释其原理或作用，避免过度简化导致失真。可以保留必要的专业术语，并通过上下文使其易于理解。
    *   **主要发现与成果**：客观、清晰地呈现论文的核心发现和结果。如果论文包含重要数据或性能指标，请准确转述，并解释其意义。
    *   **意义与应用前景**：基于论文的发现，讨论其在学术界或实际应用中可能产生的具体影响、价值和未来发展方向。这里不一定要严格按照这个格式和小标题，可以根据文章的设计进行模块化的更新，按照文章的思路介绍创新点。

4.  **行文风格**：
    *   **语言**：专业、严谨，同时保持文字的生动性和可读性。避免使用过于口语化、情绪化的表达（如过多感叹号、不必要的网络流行语）或不成熟的语气。
    *   **叙述**：逻辑清晰，条理分明，重点突出。确保信息的准确传递。
    *   **平衡性**：在专业深度和大众理解之间取得良好平衡。

5.  **字数控制**：全文（不含标题和标签）控制在800-900中文字符左右。可以分不同的段落

6.  **结尾标签**：在文章末尾，用 `标签：` 标记，另起一行提供3-5个与论文内容高度相关的中文关键词标签，用 # 分隔。例如：#人工智能 #计算机视觉 #科研进展

输出格式约定：
第一行：`标题：[你创作的标题]`
第二行开始：文章正文。
最后一行：`标签：[ #标签1 #标签2 #标签3 ]`

以下是论文的文本内容：
---
{paper_text}
---

请严格按照以上要求，创作出一篇高质量的科普解读文章。"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.6,
            "topP": 0.8,
            "topK": 40,
            "maxOutputTokens": 8192  # 允许API输出足够长的文本，之后可以在客户端侧调整
        }
    }

    try:
        response = requests.post(GEMINI_API_URL, json=payload, headers={'Content-Type': 'application/json'}, timeout=120)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("candidates") and \
           len(data["candidates"]) > 0 and \
           data["candidates"][0].get("content") and \
           data["candidates"][0]["content"].get("parts") and \
           len(data["candidates"][0]["content"]["parts"]) > 0 and \
           data["candidates"][0]["content"]["parts"][0].get("text"):
            generated_text = data["candidates"][0]["content"]["parts"][0]["text"]
            print("Gemini API调用成功！")
            return generated_text
        else:
            # 尝试打印API的原始错误信息（如果存在）
            error_details = data.get("error", {}).get("message", "API返回了无效的响应结构或没有内容")
            if not data.get("candidates") and "promptFeedback" in data: # 检查是否有promptFeedback
                 error_details = f"内容可能被安全设置阻止。Prompt Feedback: {data.get('promptFeedback')}"
            print(f"Gemini API返回内容解析错误: {error_details}")
            print(f"原始API响应: {json.dumps(data, indent=2)}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"调用Gemini API失败: {e}")
        if e.response is not None:
            print(f"API响应状态码: {e.response.status_code}")
            try:
                print(f"API响应内容: {e.response.json()}")
            except json.JSONDecodeError:
                print(f"API响应内容 (非JSON): {e.response.text}")
        return None
    except json.JSONDecodeError:
        print(f"解析Gemini API响应失败 (非JSON响应)。")
        print(f"原始API响应: {response.text}") # 打印原始文本
        return None

# 新增：文件名清理函数
def sanitize_filename(filename):
    """清理文件名中的非法字符"""
    filename = re.sub(r'[\\/*?:"<>|]',"", filename) # 移除非法字符
    filename = re.sub(r"\s+", "_", filename.strip()) # 空格替换为下划线
    return filename[:100] # 限制文件名长度

# --- 主程序 ---
if __name__ == "__main__":
    # 请将下面的URL替换为您想解读的ArXiv论文PDF链接
    # 注意：您提供的 https://arxiv.org/pdf/2505.04229 似乎是一个无效或未来的链接，
    # 它可能会导致下载失败。请使用一个有效的ArXiv PDF链接。
    # 例如: 'https://arxiv.org/pdf/2310.06825.pdf' (一个有效的示例)
    arxiv_pdf_url = input("请输入ArXiv论文的PDF链接 (例如: https://arxiv.org/pdf/2310.06825.pdf): ")

    if not arxiv_pdf_url.startswith("https://arxiv.org/pdf/"):
        print("输入的链接格式不正确，应为 https://arxiv.org/pdf/xxxx.xxxx.pdf 格式")
    else:
        pdf_data = download_pdf(arxiv_pdf_url)

        if pdf_data:
            extracted_text = extract_text_from_pdf(pdf_data)

            if extracted_text:
                # 考虑文本长度，如果过长可能需要截断或分块处理
                # Gemini API对输入文本长度有限制，但通常一篇论文的文本量可以接受
                # print(f"提取的文本（前500字符）: {extracted_text[:500]}") # 打印部分提取文本供调试

                generated_content = generate_xiaohongshu_post(extracted_text)

                if generated_content:
                    print("\n--- Gemini API 返回内容 ---")
                    print(generated_content)
                    print("--------------------------\n")

                    # 解析标题和正文
                    lines = generated_content.split('\n')
                    article_title = "未命名文章"
                    article_body = []
                    tags_line = ""
                    
                    # 确保lines非空再处理
                    if lines and lines[0].startswith("标题："):
                        article_title = lines[0].replace("标题：", "").strip()
                        content_start_index = 1
                    else:
                        print('警告：API返回内容未找到"标题："标识，将使用默认标题，并尝试保存全部返回内容。')
                        content_start_index = 0

                    for i in range(content_start_index, len(lines)):
                        if lines[i].startswith("标签："):
                            tags_line = lines[i] # 保留标签行，一起写入文件
                            break
                        article_body.append(lines[i])
                    
                    # 如果循环结束还没有找到标签行，但最后一行看起来像标签，也加入
                    # 确保 article_body 非空
                    if not tags_line and article_body and article_body[-1].strip().startswith("#"):
                         tags_line = article_body.pop() # 从body中取出作为标签行

                    final_article_text = "\n".join(article_body)
                    if tags_line: # 确保标签行存在才添加
                        final_article_text += "\n" + tags_line

                    # 获取当前日期
                    current_date = datetime.now().strftime("%Y-%m-%d")
                    
                    # 清理标题并创建文件名
                    sanitized_title = sanitize_filename(article_title)
                    if not sanitized_title: # 如果清理后标题为空，给一个默认名
                        sanitized_title = "无标题文章"
                    txt_filename = f"{current_date}_{sanitized_title}.txt"
                    
                    # 保存到TXT文件
                    try:
                        output_dir = "generated_articles"
                        if not os.path.exists(output_dir):
                            os.makedirs(output_dir)
                        
                        file_path = os.path.join(output_dir, txt_filename)
                        
                        with open(file_path, "w", encoding="utf-8") as f:
                            # 写入提取的标题（如果希望标题也在文件顶部）
                            f.write(f"标题：{article_title}\n\n")
                            f.write(final_article_text) # 写入正文和标签
                        print(f"文章已成功保存到：{file_path}")
                    except Exception as e:
                        print(f"保存文件失败: {e}")
                else:
                    print("未能生成科普文章内容。")
            else:
                print("未能从PDF中提取文本，无法继续。")
        else:
            print("未能下载PDF文件，无法继续。")
