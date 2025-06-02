import requests
from bs4 import BeautifulSoup
import PyPDF2
import io
import json
import os
from datetime import datetime
import re
import time
import random

# --- 配置区 ---
# 请注意：直接在代码中嵌入API密钥存在安全风险。
# 建议使用环境变量或其他安全方式管理您的API密钥。
API_KEY = 'AIzaSyDy9pYAEW7e2Ewk__9TCHAD5X_G1VhCtVw'  # 请替换为您的API Key
MODEL_NAME = 'gemini-2.5-flash-preview-05-20' # 假设使用 1.0 pro，如果需要flash请修改
GEMINI_API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}'

ARXIV_RECENT_CV_URL = 'https://arxiv.org/list/cs.CV/recent'
NUM_PAPERS_TO_PROCESS = 5  # 您希望每天处理的论文数量
OUTPUT_DIR = "generated_articles"  # 保存生成文章的目录
ARTICLES_INDEX_FILE = "articles_index.json" # JSON索引文件名

# --- 辅助函数 (部分从 arxiv.py 迁移和调整) ---

def sanitize_filename(filename):
    """清理文件名中的非法字符，并确保其适合文件名。"""
    if not filename:
        return "untitled_article"
    filename = str(filename) 
    filename = re.sub(r'[\\\\/\:\*\?\"\<\>\|\r\n\t]+', ' ', filename)
    filename = re.sub(r'\s+', '_', filename.strip())
    # 进一步限制文件名长度，避免过长，同时确保扩展名前的部分不为空
    base, ext = os.path.splitext(filename)
    base = base[:100].rstrip('_')
    if not base: # 如果处理后base为空（例如原名只有非法字符）
        base = "untitled_article"
    return base + ext

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
                text += page_text + "\n"
        
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
    truncated_paper_text = paper_text[:25000] # 稍微增加截断长度以包含更多上下文

    prompt = f"""作为一位资深的科技内容创作者和分析师，你的任务是根据以下科研论文的文本，撰写一篇既专业准确又不失趣味性的科普解读文章，目标读者是对科技有一定兴趣的普通大众。文章字数在500中文字符左右。

请遵循以下指导方针：

1.  **文章标题**：在解读内容的第一行，使用 `标题：` 标记。标题应精炼、引人注目，并能准确反映论文的核心贡献或最有趣的发现。

2.  **核心内容解读**：
    *   **研究动机与背景**：清晰阐述这项研究为何被提出，它针对的是什么现状或挑战。
    *   **方法与技术亮点**：用准确且易于理解的语言解释论文采用的关键方法和技术。
    *   **主要发现与成果**：客观、清晰地呈现论文的核心发现和结果。
    *   **意义与应用前景**：讨论其在学术界或实际应用中可能产生的具体影响、价值和未来发展方向。

3.  **行文风格**：专业、严谨，同时保持文字的生动性和可读性。逻辑清晰，条理分明。

4.  **字数控制**：全文（不含标题和标签）控制在500中文字符左右。

5.  **结尾标签**：在文章末尾，用 `标签：` 标记，另起一行提供3-5个与论文内容高度相关的中文关键词标签，用 # 分隔。例如：#人工智能 #计算机视觉 #科研进展

输出格式约定：
第一行：`标题：[你创作的标题]`
第二行开始：文章正文。
最后一行：`标签：[ #标签1 #标签2 #标签3 ]`

以下是论文的文本内容：
---
{truncated_paper_text}
---
请严格按照以上要求，创作出一篇高质量的科普解读文章。"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.6, # 稍降温度，追求更稳定和一致的输出
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
            error_details = "API返回了无效的响应结构或没有内容。"
            if "promptFeedback" in data and data["promptFeedback"].get("blockReason"):
                 error_details = f'内容可能被安全设置阻止。原因: {data["promptFeedback"]["blockReason"]}. 详情: {data["promptFeedback"].get("safetyRatings")}'
            elif data.get("error", {}).get("message"):
                 error_details = data["error"]["message"]
            print(f"  Gemini API返回内容解析错误: {error_details}")
            print(f"  原始API响应 (部分): {str(data)[:500]}") # 打印部分原始响应以供调试
            return None
    except requests.exceptions.Timeout:
        print("  调用Gemini API超时。")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  调用Gemini API失败: {e}")
        if e.response is not None:
            print(f"  API响应状态码: {e.response.status_code}")
            try:
                print(f"  API响应内容: {e.response.text[:500]}") # 打印部分响应文本
            except Exception:
                print("  无法打印API响应内容。")
        return None
    except json.JSONDecodeError as e:
        print(f"  解析Gemini API响应JSON失败: {e}")
        if 'response' in locals() and response is not None:
            print(f"  原始API响应文本: {response.text[:500]}")
        return None

def fetch_arxiv_papers():
    """从ArXiv获取计算机视觉论文列表，并随机抽取指定数量。"""
    print(f"正在从 {ARXIV_RECENT_CV_URL} 获取最新论文列表...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(ARXIV_RECENT_CV_URL, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        all_found_papers = [] 
        all_dl_entries = soup.find_all('dl') 
        # print(f"  (调试) 页面上共找到 {len(all_dl_entries)} 个 <dl> 条目。")

        for dl_entry in all_dl_entries:
            dt = dl_entry.find('dt')
            dd = dl_entry.find('dd')
            
            if not dt or not dd:
                continue

            pdf_link_tag = dt.find('a', href=re.compile(r'/pdf/'), title='Download PDF')
            title_div = dd.find('div', class_='list-title')
            
            if pdf_link_tag and title_div:
                pdf_url = 'https://arxiv.org' + pdf_link_tag['href']
                title_span = title_div.find('span', class_='descriptor')
                if title_span:
                    title_span.extract() 
                
                raw_title = title_div.text.strip()
                
                if not any(p_url == pdf_url for p_url, _ in all_found_papers):
                    all_found_papers.append((pdf_url, raw_title))

        if not all_found_papers:
            print("未能从ArXiv页面提取到任何符合条件的论文信息。")
            return []
            
        print(f"成功从页面提取到 {len(all_found_papers)} 篇符合条件的论文信息。")

        if len(all_found_papers) > NUM_PAPERS_TO_PROCESS:
            print(f"  论文数量 ({len(all_found_papers)}) 大于目标处理数 ({NUM_PAPERS_TO_PROCESS})，将进行随机抽取。")
            selected_papers = random.sample(all_found_papers, NUM_PAPERS_TO_PROCESS)
        else:
            print(f"  论文数量 ({len(all_found_papers)}) 不大于目标处理数 ({NUM_PAPERS_TO_PROCESS})，将处理所有找到的论文。")
            selected_papers = all_found_papers
        
        print(f"最终选定 {len(selected_papers)} 篇论文进行处理。")
        return selected_papers

    except requests.exceptions.RequestException as e:
        print(f"获取ArXiv页面失败: {e}")
        return []
    except Exception as e:
        print(f"解析ArXiv页面时发生错误: {e}")
        return []

# --- 主处理逻辑 ---
def process_and_save_paper(pdf_url, original_title):
    """
    下载、处理单篇论文并保存生成的文章。
    返回一个包含文章信息的字典，如果处理失败则返回 None。
    """
    print(f"处理论文: {original_title} ({pdf_url})")
    
    pdf_content = download_pdf(pdf_url)
    if not pdf_content:
        return None

    extracted_text = extract_text_from_pdf(pdf_content)
    if not extracted_text:
        return None

    generated_article_raw = generate_pop_science_article(extracted_text)
    if not generated_article_raw:
        print("  未能生成科普文章内容，跳过保存。")
        return None

    lines = generated_article_raw.split('\n')
    api_title_str = None
    article_body_lines = []
    tags_line_str = "" # Initialize as empty string

    if lines and lines[0].startswith("标题："):
        api_title_str = lines[0].replace("标题：", "").strip()
        article_body_lines = lines[1:] # All subsequent lines could be body or tags
    else:
        article_body_lines = lines # No "标题：" prefix, assume all is body or tags
    
    # Separate body and tags
    temp_body = []
    for i, line in enumerate(article_body_lines):
        if line.startswith("标签："):
            tags_line_str = line
            # temp_body.extend(article_body_lines[:i]) # This was incorrect logic
            break # Tags found, stop adding to body
        temp_body.append(line)
    
    final_article_body = "\n".join(temp_body).strip() # Join only the actual body lines

    filename_title = api_title_str if api_title_str else original_title
    if not filename_title: # Fallback if both are None or empty
        filename_title = "Untitled_Article"

    current_date_str = datetime.now().strftime("%Y-%m-%d")
    sanitized_title_for_filename = sanitize_filename(filename_title)
    
    txt_filename_only = f"{current_date_str}_{sanitized_title_for_filename}.txt"
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    txt_file_full_path = os.path.join(OUTPUT_DIR, txt_filename_only)
    
    try:
        with open(txt_file_full_path, "w", encoding="utf-8") as f:
            f.write(f"标题：{filename_title}\n\n") 
            f.write(final_article_body)
            if tags_line_str: # Append tags if found
                f.write(f"\n\n{tags_line_str}")
        print(f"  文章已成功保存到： {txt_file_full_path}")

        arxiv_id_match = re.search(r'pdf/([\d\.]+)', pdf_url)
        arxiv_id = arxiv_id_match.group(1) if arxiv_id_match else "unknown"
        
        relative_txt_path = os.path.join(OUTPUT_DIR, txt_filename_only).replace(os.path.sep, '/')


        article_info = {
            "title": filename_title,
            "arxiv_id": arxiv_id,
            "pdf_url": pdf_url,
            "txt_filename": txt_filename_only,
            "txt_file_path_relative": relative_txt_path,
            "date_processed": current_date_str,
            "tags": tags_line_str.replace("标签：", "").replace("[", "").replace("]", "").strip() if tags_line_str else "",
            "image_dir": None, 
            "first_page_image": None
        }
        return article_info
    except Exception as e:
        print(f"  保存文件失败: {e}")
        return None

# --- 主处理逻辑 ---
if __name__ == "__main__":
    print("开始每日ArXiv论文处理任务...")
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"创建输出目录: {OUTPUT_DIR}")

    articles_index_full_path = os.path.join(OUTPUT_DIR, ARTICLES_INDEX_FILE)
    all_articles_info = []

    if os.path.exists(articles_index_full_path):
        try:
            with open(articles_index_full_path, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip(): # Check if file is not empty
                    all_articles_info = json.loads(content)
                    if not isinstance(all_articles_info, list):
                        print(f"警告：{articles_index_full_path} 内容不是一个列表，将重新开始。")
                        all_articles_info = []
                    else:
                        print(f"已从 {articles_index_full_path} 加载 {len(all_articles_info)} 条现有文章记录。")
                else:
                    print(f"{articles_index_full_path} 为空，将初始化新的索引。")
                    all_articles_info = []
        except json.JSONDecodeError:
            print(f"警告：无法解析 {articles_index_full_path}。将创建一个新的索引文件。")
            all_articles_info = []
        except Exception as e:
            print(f"读取 {articles_index_full_path} 时发生错误: {e}。将创建一个新的索引文件。")
            all_articles_info = []
    else:
        print(f"索引文件 {articles_index_full_path} 不存在，将创建新的索引。")
    
    existing_pdf_urls = {article.get("pdf_url") for article in all_articles_info if article.get("pdf_url")}

    papers_to_fetch_and_process = fetch_arxiv_papers()
    
    newly_processed_articles_this_run = []

    if papers_to_fetch_and_process:
        for i, (pdf_url, title) in enumerate(papers_to_fetch_and_process):
            print(f"\n--- 正在处理选定的第 {i+1}/{len(papers_to_fetch_and_process)} 篇论文 ---")
            
            if pdf_url in existing_pdf_urls:
                print(f"  论文 {pdf_url} (标题: {title}) 已存在于索引中，跳过处理。")
                continue

            article_data = process_and_save_paper(pdf_url, title)
            if article_data:
                newly_processed_articles_this_run.append(article_data)
                existing_pdf_urls.add(pdf_url) 
            
            if i < len(papers_to_fetch_and_process) - 1: # Don't sleep after the last paper
                print("  等待5秒，避免过于频繁请求...") # Reduced sleep time
                time.sleep(5) 
    else:
        print("没有从ArXiv提取到符合条件的论文进行处理。")
        
    if newly_processed_articles_this_run:
        print(f"\n本次运行新处理并保存了 {len(newly_processed_articles_this_run)} 篇文章。")
        all_articles_info.extend(newly_processed_articles_this_run)
        
        try:
            with open(articles_index_full_path, "w", encoding="utf-8") as f:
                json.dump(all_articles_info, f, ensure_ascii=False, indent=4)
            print(f"文章索引已更新并保存到: {articles_index_full_path} (共 {len(all_articles_info)} 条记录)")
        except Exception as e:
            print(f"保存文章索引到 {articles_index_full_path} 失败: {e}")
    elif not all_articles_info and not os.path.exists(articles_index_full_path):
        # If no articles ever existed and none were processed, create an empty JSON list file
        try:
            with open(articles_index_full_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=4)
            print(f"创建了空的索引文件: {articles_index_full_path}")
        except Exception as e:
            print(f"创建空索引文件 {articles_index_full_path} 失败: {e}")
    else:
        print("\n本次运行没有新处理的文章被添加到索引中。")

    print("\n每日ArXiv论文处理任务完成。") 