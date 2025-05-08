import requests
from bs4 import BeautifulSoup
import PyPDF2
import io
import json
import os
from datetime import datetime
import re
import time

# --- 配置区 ---
# 请注意：直接在代码中嵌入API密钥存在安全风险。
# 建议使用环境变量或其他安全方式管理您的API密钥。
API_KEY = 'AIzaSyDy9pYAEW7e2Ewk__9TCHAD5X_G1VhCtVw'  # 您提供的API Key
MODEL_NAME = 'gemini-2.0-flash-exp'  # 您提供的模型名称
GEMINI_API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}'

ARXIV_RECENT_CV_URL = 'https://arxiv.org/list/cs.CV/recent'
NUM_PAPERS_TO_PROCESS = 5  # 您希望每天处理的论文数量
OUTPUT_DIR = "generated_articles"  # 保存生成文章的目录

# --- 辅助函数 (部分从 arxiv.py 迁移和调整) ---

def sanitize_filename(filename):
    """清理文件名中的非法字符，并确保其适合文件名。"""
    if not filename:
        return "untitled_article"
    # 移除路径相关的斜杠和可能引起问题的字符
    filename = re.sub(r'[\\\\/\:\*\?\"\<\>\|\r\n\t]+', ' ', filename)
    # 将多个空格替换为单个下划线
    filename = re.sub(r'\s+', '_', filename.strip())
    return filename[:100]  # 限制文件名长度，避免过长

def download_pdf(pdf_url):
    """下载PDF文件并返回其二进制内容"""
    print(f"  正在从 {pdf_url} 下载PDF...")
    try:
        response = requests.get(pdf_url, timeout=60)
        response.raise_for_status()
        print("  PDF下载成功！")
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"  下载PDF失败: {e}")
        return None

def extract_text_from_pdf(pdf_content):
    """从PDF的二进制内容中提取文本"""
    print("  正在提取PDF文本...")
    text = ""
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        if not pdf_reader.pages:
            print("  警告：PDF文件不包含任何页面或无法读取页面。")
            return None
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"  # 添加换行符以分隔页面文本
        
        if not text.strip():
            print("  警告：提取到的文本为空。PDF可能是图片格式、内容无法识别或加密。")
            return None
        print(f"  PDF文本提取完成，共提取约 {len(text)} 字符。")
        return text
    except PyPDF2.errors.PdfReadError as e:
        print(f"  提取PDF文本失败 (PdfReadError): {e}. PDF可能已损坏或加密。")
        return None
    except Exception as e:
        print(f"  提取PDF文本时发生意外错误: {e}")
        return None

def generate_pop_science_article(paper_text):
    """调用Gemini API生成科普风格的论文解读"""
    print("  正在调用Gemini API生成科普文章...")

    # Gemini API对输入文本长度有限制，截断一部分，避免超长
    # 20000字符约等于10000到15000个英文单词，或5000到10000个中文字，通常够用
    truncated_paper_text = paper_text[:20000]

    prompt = f"""作为一位资深的科技内容创作者和分析师，你的任务是根据以下科研论文的文本，撰写一篇既专业准确又不失趣味性的科普解读文章，目标读者是对科技有一定兴趣的普通大众。文章字数在500中文字符左右。

请遵循以下指导方针：

1.  **文章标题**：在解读内容的第一行，使用 `标题：` 标记。标题应精炼、引人注目，并能准确反映论文的核心贡献或最有趣的发现。例如："AI新突破：机器视觉首次实现X功能"或"深度解析：Y理论如何颠覆我们对Z的认知"。

2.  **开篇**：用简洁的几句话点明研究的背景、试图解决的关键问题及其潜在的重要性或新奇之处，以吸引读者继续阅读。

3.  **核心内容解读**：
    *   **研究动机与背景**：清晰阐述这项研究为何被提出，它针对的是什么现状或挑战。
    *   **方法与技术亮点**：用准确且易于理解的语言解释论文采用的关键方法和技术。如果涉及复杂概念，尝试用简明的方式解释其原理或作用，避免过度简化导致失真。可以保留必要的专业术语，并通过上下文使其易于理解。
    *   **主要发现与成果**：客观、清晰地呈现论文的核心发现和结果。如果论文包含重要数据或性能指标，请准确转述，并解释其意义。
    *   **意义与应用前景**：基于论文的发现，讨论其在学术界或实际应用中可能产生的具体影响、价值和未来发展方向。

4.  **行文风格**：
    *   **语言**：专业、严谨，同时保持文字的生动性和可读性。避免使用过于口语化、情绪化的表达（如过多感叹号、不必要的网络流行语）或不成熟的语气。
    *   **叙述**：逻辑清晰，条理分明，重点突出。确保信息的准确传递。
    *   **平衡性**：在专业深度和大众理解之间取得良好平衡。

5.  **字数控制**：全文（不含标题和标签）控制在500中文字符左右。

6.  **结尾标签**：在文章末尾，用 `标签：` 标记，另起一行提供3-5个与论文内容高度相关的中文关键词标签，用 # 分隔。例如：#人工智能 #计算机视觉 #科研进展

输出格式约定：
第一行：`标题：[你创作的标题]`
第二行开始：文章正文。
最后一行：`标签：[ #标签1 #标签2 #标签3 ]`

以下是论文的文本内容：
---
{truncated_paper_text}
---
(提示：输入文本为论文部分内容摘要，请基于此进行创作。)

请严格按照以上要求，创作出一篇高质量的科普解读文章。"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7, 
            "topP": 0.8,
            "topK": 40,
            "maxOutputTokens": 2048 
        }
    }

    try:
        response = requests.post(GEMINI_API_URL, json=payload, headers={'Content-Type': 'application/json'}, timeout=180)
        response.raise_for_status()
        data = response.json()
        
        if data.get("candidates") and data["candidates"][0].get("content") and data["candidates"][0]["content"]["parts"][0].get("text"):
            generated_text = data["candidates"][0]["content"]["parts"][0]["text"]
            print("  Gemini API调用成功！")
            return generated_text
        else:
            error_details = data.get("error", {}).get("message", "API返回了无效的响应结构或没有内容")
            if not data.get("candidates") and "promptFeedback" in data:
                 error_details = f'内容可能被安全设置阻止。Prompt Feedback: {data.get("promptFeedback")}'
            print(f"  Gemini API返回内容解析错误: {error_details}")
            print(f"  原始API响应: {json.dumps(data, indent=2)}")
            return None
    except requests.exceptions.Timeout:
        print("  调用Gemini API超时。")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  调用Gemini API失败: {e}")
        if e.response is not None:
            print(f"  API响应状态码: {e.response.status_code}")
            try:
                print(f"  API响应内容: {e.response.json()}")
            except json.JSONDecodeError:
                print(f"  API响应内容 (非JSON): {e.response.text}")
        return None
    except json.JSONDecodeError as e:
        print(f"  解析Gemini API响应JSON失败: {e}")
        if 'response' in locals() and response is not None:
            print(f"  原始API响应文本: {response.text}")
        return None

def fetch_arxiv_papers():
    """从ArXiv获取最新的计算机视觉论文列表"""
    print(f"正在从 {ARXIV_RECENT_CV_URL} 获取最新论文列表...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(ARXIV_RECENT_CV_URL, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        papers = []
        print(f"  (调试) NUM_PAPERS_TO_PROCESS 设置为: {NUM_PAPERS_TO_PROCESS}")
        # ArXiv 使用 <dl> 标签包裹每篇论文信息
        # 获取比需求多一些的条目以进行筛选
        all_dl_entries = soup.find_all('dl') 
        print(f"  (调试) 页面上共找到 {len(all_dl_entries)} 个 <dl> 条目。")

        processed_entry_count = 0
        for dl_entry in all_dl_entries:
            if len(papers) >= NUM_PAPERS_TO_PROCESS:
                print(f"  (调试) 已收集到 {len(papers)} 篇论文，达到目标数量，停止查找。")
                break
            
            processed_entry_count += 1
            print(f"\n  (调试) 正在检查第 {processed_entry_count} 个 <dl> 条目...")

            dt = dl_entry.find('dt')
            dd = dl_entry.find('dd')
            
            if not dt:
                print("    (调试) 未找到 <dt> 标签，跳过此条目。")
                continue
            if not dd:
                print("    (调试) 未找到 <dd> 标签，跳过此条目。")
                continue

            pdf_link_tag = dt.find('a', href=re.compile(r'/pdf/'), title='Download PDF')
            title_div = dd.find('div', class_='list-title')
            
            if not pdf_link_tag:
                print("    (调试) 未找到PDF链接标签 (<a> with href containing /pdf/ and title 'Download PDF')。")
            if not title_div:
                print("    (调试) 未找到标题DIV (<div class=\'list-title\'>)。")

            if pdf_link_tag and title_div:
                pdf_url = 'https://arxiv.org' + pdf_link_tag['href']
                title_span = title_div.find('span', class_='descriptor')
                if title_span:
                    title_span.extract() 
                
                raw_title = title_div.text.strip()
                print(f"    (调试) 潜在论文：'{raw_title}' - {pdf_url}")
                
                is_duplicate = any(p_url == pdf_url for p_url, _ in papers)
                if is_duplicate:
                    print("    (调试) 此论文URL已存在，跳过重复项。")
                    continue
                
                papers.append((pdf_url, raw_title))
                print("    (调试) 成功添加论文到列表。")
            else:
                print("    (调试) 因缺少PDF链接或标题DIV，此条目不符合要求，跳过。")

        if not papers:
            print("未能从ArXiv页面提取到任何符合条件的论文信息。")
            return []
            
        print(f"成功提取到 {len(papers)} 篇符合条件的论文信息。")
        return papers[:NUM_PAPERS_TO_PROCESS] # 确保只返回所需数量，即使提取的更多

    except requests.exceptions.RequestException as e:
        print(f"获取ArXiv页面失败: {e}")
        return []
    except Exception as e:
        print(f"解析ArXiv页面时发生错误: {e}")
        return []

# --- 主处理逻辑 ---
def process_and_save_paper(pdf_url, original_title):
    """下载、处理单篇论文并保存生成的文章"""
    print(f"处理论文: {original_title} ({pdf_url})")
    
    pdf_content = download_pdf(pdf_url)
    if not pdf_content:
        return

    extracted_text = extract_text_from_pdf(pdf_content)
    if not extracted_text:
        return

    generated_article_raw = generate_pop_science_article(extracted_text)
    if not generated_article_raw:
        print("  未能生成科普文章内容，跳过保存。")
        return

    print("\n--- Gemini API 返回的原始文章 ---")
    print(generated_article_raw)
    print("--------------------------------\n")

    lines = generated_article_raw.split('\n')
    api_title = None
    article_body_lines = []
    tags_line = ""
    content_start_index = 0

    if lines and lines[0].startswith("标题："):
        api_title = lines[0].replace("标题：", "").strip()
        content_start_index = 1
        print(f"  API提取标题：'{api_title}'")
    else:
        print("  警告：API返回内容未找到预期的'标题：'标识。将使用ArXiv原标题。")
    
    filename_title = api_title if api_title else original_title

    for i in range(content_start_index, len(lines)):
        line = lines[i]
        if line.startswith("标签："):
            tags_line = line 
            break 
        article_body_lines.append(line)
    
    final_article_text = "\n".join(article_body_lines)
    if tags_line:
        final_article_text += "\n\n" + tags_line
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    sanitized_title_for_filename = sanitize_filename(filename_title)
    
    txt_filename = f"{current_date}_{sanitized_title_for_filename}.txt"
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    file_path = os.path.join(OUTPUT_DIR, txt_filename)
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"标题：{filename_title}\n\n") 
            f.write(final_article_text)
        print(f"  文章已成功保存到： {file_path}")
    except Exception as e:
        print(f"  保存文件失败: {e}")

if __name__ == "__main__":
    print("开始每日ArXiv论文处理任务...")
    
    papers_to_process = fetch_arxiv_papers()
    
    if papers_to_process:
        for i, (pdf_url, title) in enumerate(papers_to_process):
            print(f"\n--- 正在处理第 {i+1}/{len(papers_to_process)} 篇论文 ---")
            process_and_save_paper(pdf_url, title)
            if i < len(papers_to_process) - 1:
                print("  等待10秒，避免过于频繁请求...")
                time.sleep(10) 
    else:
        print("没有提取到论文，任务结束。")
        
    print("\n每日ArXiv论文处理任务完成。") 