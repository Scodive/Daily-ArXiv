#!/usr/bin/env python3
"""
每日自动论文处理脚本
功能：自动获取ArXiv最新论文，生成科普文章并保存到数据库

使用方法：
python daily_auto.py

可选参数：
--count N    处理N篇论文 (默认3)
--category X 指定分类 (默认cs.AI)
--force      强制重新处理已存在的论文
"""

import requests
import sys
import argparse
from datetime import datetime, timedelta
import time
import random
import re
from arxiv import (
    download_pdf, 
    extract_text_from_pdf, 
    generate_xiaohongshu_post,
    sanitize_filename,
    insert_article_to_database,
    extract_arxiv_id_from_url
)
import os

def get_today_arxiv_papers_from_rss(categories=["cs.AI"]):
    """
    从ArXiv RSS feed获取今天的新论文
    
    Args:
        categories: 分类列表 (如 ["cs.AI", "cs.CV", "cs.CL"])
    
    Returns:
        list: 论文信息列表
    """
    print(f"🔍 正在从ArXiv RSS获取今天的论文，分类: {categories}")
    
    all_papers = []
    
    # ArXiv RSS URL格式：https://rss.arxiv.org/rss/{category}
    for category in categories:
        print(f"📚 正在获取 {category} 分类的RSS...")
        
        try:
            rss_url = f"https://rss.arxiv.org/rss/{category}"
            print(f"   RSS URL: {rss_url}")
            
            response = requests.get(rss_url, timeout=30)
            response.raise_for_status()
            
            # 解析RSS XML
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            category_papers = []
            
            # RSS中的item元素包含论文信息
            for item in root.findall('.//item'):
                try:
                    # 获取标题
                    title_elem = item.find('title')
                    if title_elem is None:
                        continue
                    
                    clean_title = title_elem.text.strip()
                    
                    # 获取链接和ArXiv ID
                    link_elem = item.find('link')
                    if link_elem is None:
                        continue
                    
                    abs_url = link_elem.text.strip()
                    # 从链接中提取ArXiv ID：https://arxiv.org/abs/2506.05352
                    arxiv_match = re.search(r'arxiv\.org/abs/([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)', abs_url)
                    if not arxiv_match:
                        continue
                    
                    arxiv_id = arxiv_match.group(1)
                    
                    # 从abstract链接构造PDF链接
                    pdf_url = abs_url.replace('/abs/', '/pdf/') + '.pdf'
                    
                    # 获取描述（摘要）
                    desc_elem = item.find('description')
                    summary = ""
                    if desc_elem is not None and desc_elem.text:
                        desc_text = desc_elem.text.strip()
                        
                        # 提取摘要部分：在"Abstract:"之后的内容
                        abstract_match = re.search(r'Abstract:\s*(.+)', desc_text, re.DOTALL)
                        if abstract_match:
                            summary = abstract_match.group(1).strip()
                        else:
                            summary = desc_text
                        
                        # 清理多余空格和换行
                        summary = re.sub(r'\s+', ' ', summary)
                    
                    # 获取发布日期
                    pub_date_elem = item.find('pubDate')
                    pub_date = datetime.now()  # 默认为当前时间
                    if pub_date_elem is not None:
                        try:
                            # RSS日期格式：Mon, 09 Jun 2025 00:00:00 -0400
                            from email.utils import parsedate_to_datetime
                            pub_date = parsedate_to_datetime(pub_date_elem.text)
                        except:
                            pub_date = datetime.now()
                    
                    paper_info = {
                        'title': clean_title,
                        'pdf_url': pdf_url,
                        'arxiv_id': arxiv_id,
                        'published': pub_date,
                        'categories': [category],
                        'primary_category': category,
                        'summary': summary[:500] + '...' if len(summary) > 500 else summary
                    }
                    
                    category_papers.append(paper_info)
                    
                except Exception as e:
                    print(f"   ⚠️  解析论文条目失败: {e}")
                    continue
            
            print(f"   ✅ {category} 分类找到 {len(category_papers)} 篇论文")
            all_papers.extend(category_papers)
            
        except Exception as e:
            print(f"   ❌ 获取 {category} RSS失败: {e}")
    
    # 去重（按ArXiv ID）
    unique_papers = {}
    for paper in all_papers:
        arxiv_id = paper['arxiv_id']
        if arxiv_id not in unique_papers:
            unique_papers[arxiv_id] = paper
    
    result_papers = list(unique_papers.values())
    print(f"✅ 总共找到 {len(result_papers)} 篇唯一论文")
    return result_papers

def get_today_arxiv_papers_by_category_api(categories=["cs.AI"], max_results_per_category=100):
    """
    使用改进的API查询获取最近提交的ArXiv论文
    
    Args:
        categories: 分类列表
        max_results_per_category: 每个分类的最大结果数
    
    Returns:
        list: 论文信息列表
    """
    print(f"🔍 正在使用API获取最新ArXiv论文，分类: {categories}")
    
    all_papers = []
    
    for category in categories:
        print(f"📚 正在获取 {category} 分类的论文...")
        
        try:
            # ArXiv API URL - 不用日期过滤，获取最新的论文
            base_url = "http://export.arxiv.org/api/query"
            
            # 简化查询 - 只按分类，按最新排序
            query = f"cat:{category}"
            params = {
                "search_query": query,
                "start": 0,
                "max_results": max_results_per_category,
                "sortBy": "submittedDate",
                "sortOrder": "descending"
            }
            
            print(f"   查询: {query}")
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            
            # 解析XML响应
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            category_papers = []
            today = datetime.now().date()
            
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                # 提取论文信息
                title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
                title = re.sub(r'\s+', ' ', title)  # 清理多余空格
                
                # 获取PDF链接
                pdf_link = None
                for link in entry.findall('{http://www.w3.org/2005/Atom}link'):
                    if link.get('type') == 'application/pdf':
                        pdf_link = link.get('href')
                        break
                
                # 获取发布日期
                published = entry.find('{http://www.w3.org/2005/Atom}published').text
                pub_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                
                # 只保留今天或最近1-2天的论文
                days_diff = (datetime.now().date() - pub_date.date()).days
                if days_diff > 2:  # 超过2天的跳过
                    continue
                
                # 获取ArXiv ID
                arxiv_id = entry.find('{http://www.w3.org/2005/Atom}id').text
                arxiv_id = arxiv_id.split('/')[-1]  # 提取ID部分
                
                # 获取分类信息
                categories_list = []
                for category_elem in entry.findall('{http://www.w3.org/2005/Atom}category'):
                    categories_list.append(category_elem.get('term'))
                
                # 获取摘要
                summary = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
                summary = re.sub(r'\s+', ' ', summary)  # 清理多余空格
                
                paper_info = {
                    'title': title,
                    'pdf_url': pdf_link,
                    'arxiv_id': arxiv_id,
                    'published': pub_date,
                    'categories': categories_list,
                    'primary_category': category,
                    'summary': summary[:500] + '...' if len(summary) > 500 else summary
                }
                
                category_papers.append(paper_info)
            
            print(f"   ✅ {category} 分类找到 {len(category_papers)} 篇最近论文")
            all_papers.extend(category_papers)
            
        except Exception as e:
            print(f"   ❌ 获取 {category} 分类论文失败: {e}")
    
    # 去重（按ArXiv ID）
    unique_papers = {}
    for paper in all_papers:
        arxiv_id = paper['arxiv_id']
        if arxiv_id not in unique_papers:
            unique_papers[arxiv_id] = paper
    
    result_papers = list(unique_papers.values())
    print(f"✅ 总共找到 {len(result_papers)} 篇唯一论文")
    return result_papers

def get_recent_arxiv_papers_fallback(categories=["cs.AI"], max_results=100, days_back=3):
    """
    后备方案：获取最近几天的论文（如果今天没有论文）
    
    Args:
        categories: 分类列表
        max_results: 最大结果数
        days_back: 向前查找天数
    
    Returns:
        list: 论文信息列表
    """
    print(f"🔄 使用后备方案：获取最近{days_back}天的论文...")
    
    all_papers = []
    
    for category in categories:
        try:
            base_url = "http://export.arxiv.org/api/query"
            
            # 构建查询参数
            query = f"cat:{category}"
            params = {
                "search_query": query,
                "start": 0,
                "max_results": max_results,
                "sortBy": "submittedDate",
                "sortOrder": "descending"
            }
            
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            
            # 解析XML响应
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                # 获取发布日期
                published = entry.find('{http://www.w3.org/2005/Atom}published').text
                pub_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                
                # 只保留最近几天的论文
                if pub_date >= start_date.replace(tzinfo=pub_date.tzinfo):
                    # 提取论文信息
                    title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
                    title = re.sub(r'\s+', ' ', title)
                    
                    # 获取PDF链接
                    pdf_link = None
                    for link in entry.findall('{http://www.w3.org/2005/Atom}link'):
                        if link.get('type') == 'application/pdf':
                            pdf_link = link.get('href')
                            break
                    
                    # 获取ArXiv ID
                    arxiv_id = entry.find('{http://www.w3.org/2005/Atom}id').text
                    arxiv_id = arxiv_id.split('/')[-1]
                    
                    # 获取分类信息
                    categories_list = []
                    for category_elem in entry.findall('{http://www.w3.org/2005/Atom}category'):
                        categories_list.append(category_elem.get('term'))
                    
                    # 获取摘要
                    summary = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
                    summary = re.sub(r'\s+', ' ', summary)
                    
                    all_papers.append({
                        'title': title,
                        'pdf_url': pdf_link,
                        'arxiv_id': arxiv_id,
                        'published': pub_date,
                        'categories': categories_list,
                        'primary_category': category,
                        'summary': summary[:500] + '...' if len(summary) > 500 else summary
                    })
            
        except Exception as e:
            print(f"❌ 获取 {category} 分类论文失败: {e}")
    
    # 去重
    unique_papers = {}
    for paper in all_papers:
        arxiv_id = paper['arxiv_id']
        if arxiv_id not in unique_papers:
            unique_papers[arxiv_id] = paper
    
    result_papers = list(unique_papers.values())
    print(f"✅ 后备方案找到 {len(result_papers)} 篇论文")
    return result_papers

def check_paper_exists_in_db(arxiv_id, title):
    """检查论文是否已存在于数据库"""
    try:
        from arxiv import connect_to_database
        conn = connect_to_database()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        if arxiv_id:
            cursor.execute("SELECT id FROM articles WHERE arxiv_id = %s", (arxiv_id,))
        else:
            cursor.execute("SELECT id FROM articles WHERE title = %s", (title,))
        
        exists = cursor.fetchone() is not None
        
        cursor.close()
        conn.close()
        
        return exists
        
    except Exception as e:
        print(f"⚠️  检查数据库失败: {e}")
        return False

def process_single_paper(paper_info, force_process=False):
    """
    处理单篇论文
    
    Args:
        paper_info: 论文信息字典
        force_process: 是否强制处理已存在的论文
    
    Returns:
        bool: 处理是否成功
    """
    title = paper_info['title']
    pdf_url = paper_info['pdf_url']
    arxiv_id = paper_info['arxiv_id']
    
    print(f"\n📄 正在处理论文: {title[:60]}...")
    
    # 检查是否已存在（除非强制处理）
    if not force_process and check_paper_exists_in_db(arxiv_id, title):
        print(f"⚠️  论文已存在，跳过处理")
        return True
    
    try:
        # 下载PDF
        pdf_data = download_pdf(pdf_url)
        if not pdf_data:
            print("❌ PDF下载失败")
            return False
        
        # 提取文本
        extracted_text = extract_text_from_pdf(pdf_data)
        if not extracted_text or len(extracted_text.strip()) < 100:
            print("❌ PDF文本提取失败或内容太少")
            return False
        
        print(f"✅ 成功提取 {len(extracted_text)} 字符的文本")
        
        # 生成科普文章
        generated_content = generate_xiaohongshu_post(extracted_text)
        if not generated_content:
            print("❌ 科普文章生成失败")
            return False
        
        print("✅ 科普文章生成成功")
        
        # 解析生成的内容
        lines = generated_content.split('\n')
        article_title = title  # 默认使用原标题
        article_body = []
        tags_line = ""
        
        # 查找生成的标题
        if lines and lines[0].startswith("标题："):
            article_title = lines[0].replace("标题：", "").strip()
            content_start_index = 1
        else:
            content_start_index = 0
        
        # 分离正文和标签
        for i in range(content_start_index, len(lines)):
            if lines[i].startswith("标签："):
                tags_line = lines[i]
                break
            article_body.append(lines[i])
        
        if not tags_line and article_body and article_body[-1].strip().startswith("#"):
            tags_line = article_body.pop()
        
        final_article_text = "\n".join(article_body)
        if tags_line:
            final_article_text += "\n" + tags_line
        
        # 保存到本地文件
        current_date = datetime.now().strftime("%Y-%m-%d")
        sanitized_title = sanitize_filename(article_title)
        if not sanitized_title:
            sanitized_title = f"arxiv_{arxiv_id}"
        
        txt_filename = f"{current_date}_{sanitized_title}.txt"
        
        # 确保输出目录存在
        output_dir = "generated_articles"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        file_path = os.path.join(output_dir, txt_filename)
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"标题：{article_title}\n\n")
                f.write(final_article_text)
            print(f"📄 文章已保存到: {file_path}")
        except Exception as e:
            print(f"⚠️  文件保存失败: {e}")
        
        # 保存到数据库
        content_for_db = final_article_text
        tags_for_db = tags_line.replace("标签：", "").strip() if tags_line else ""
        date_processed = datetime.now().date()
        
        db_success = insert_article_to_database(
            title=article_title,
            content=content_for_db,
            tags=tags_for_db,
            arxiv_id=arxiv_id,
            pdf_url=pdf_url,
            filename=txt_filename,
            date_processed=date_processed
        )
        
        if db_success:
            print("🎉 论文处理完成！")
            return True
        else:
            print("⚠️  文件已保存，但数据库保存失败")
            return False
            
    except Exception as e:
        print(f"❌ 处理论文时发生错误: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='每日自动论文处理脚本')
    parser.add_argument('--count', type=int, default=5, help='处理论文数量 (默认5)')
    parser.add_argument('--categories', nargs='+', default=['cs.AI'], 
                       help='ArXiv分类列表 (默认cs.AI, 可指定多个如: cs.AI cs.CV cs.CL)')
    parser.add_argument('--force', action='store_true', help='强制重新处理已存在的论文')
    parser.add_argument('--fallback-days', type=int, default=3, help='后备方案查找天数 (默认3)')
    
    args = parser.parse_args()
    
    print("🤖 每日ArXiv论文自动处理脚本启动")
    print(f"📊 配置: 分类={args.categories}, 数量={args.count}, 强制={args.force}")
    print("-" * 60)
    
    # 尝试多种方法获取论文
    papers = []
    
    # 方法1：RSS feed (优先，因为RSS总是包含最新论文)
    print("🔄 方法1: 尝试从RSS feed获取论文...")
    try:
        papers = get_today_arxiv_papers_from_rss(categories=args.categories)
        if papers:
            print(f"✅ RSS方法成功获取到 {len(papers)} 篇论文")
        else:
            print("⚠️ RSS方法未获取到论文")
    except Exception as e:
        print(f"❌ RSS方法失败: {e}")
    
    # 方法2：API查询 (如果RSS失败或结果太少)
    if len(papers) < 5:
        print("🔄 方法2: 尝试API查询获取更多论文...")
        try:
            api_papers = get_today_arxiv_papers_by_category_api(
                categories=args.categories,
                max_results_per_category=20
            )
            
            # 合并结果，去重
            existing_ids = set(p['arxiv_id'] for p in papers)
            for paper in api_papers:
                if paper['arxiv_id'] not in existing_ids:
                    papers.append(paper)
                    existing_ids.add(paper['arxiv_id'])
            
            print(f"✅ 合并后总共有 {len(papers)} 篇论文")
            
        except Exception as e:
            print(f"❌ API方法失败: {e}")
    
    # 方法3：后备方案 (如果前两种方法都失败)
    if len(papers) < 2:
        print("🔄 方法3: 使用后备方案...")
        try:
            fallback_papers = get_recent_arxiv_papers_fallback(
                categories=args.categories,
                max_results=args.count * 5,  # 获取更多以防处理失败
                days_back=args.fallback_days
            )
            
            existing_ids = set(p['arxiv_id'] for p in papers)
            for paper in fallback_papers:
                if paper['arxiv_id'] not in existing_ids:
                    papers.append(paper)
                    existing_ids.add(paper['arxiv_id'])
            
            print(f"✅ 最终总共有 {len(papers)} 篇论文")
            
        except Exception as e:
            print(f"❌ 后备方案失败: {e}")
    
    if not papers:
        print("❌ 没有找到可处理的论文")
        return
    
    # 按发布时间排序，最新的在前
    papers.sort(key=lambda x: x['published'], reverse=True)
    
    print(f"\n📚 准备处理 {len(papers)} 篇候选论文，目标处理 {args.count} 篇")
    
    # 处理论文
    success_count = 0
    total_processed = 0
    processed_categories = set()
    
    for i, paper in enumerate(papers):
        if total_processed >= args.count:
            break
        
        print(f"\n{'='*60}")
        print(f"处理进度: {total_processed + 1}/{args.count}")
        print(f"📄 论文: {paper['title'][:60]}...")
        print(f"🏷️  分类: {', '.join(paper.get('categories', [paper.get('primary_category', 'unknown')]))}")
        print(f"🆔 ArXiv ID: {paper['arxiv_id']}")
        print(f"📅 发布时间: {paper['published'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        success = process_single_paper(paper, args.force)
        total_processed += 1
        
        if success:
            success_count += 1
            processed_categories.add(paper.get('primary_category', 'unknown'))
        
        # 在处理之间添加延迟，避免过快请求API
        if i < len(papers) - 1 and total_processed < args.count:
            delay = random.randint(8, 20)
            print(f"⏰ 等待 {delay} 秒后处理下一篇...")
            time.sleep(delay)
    
    print(f"\n🎯 处理完成!")
    print(f"📊 总计处理: {total_processed} 篇")
    print(f"✅ 成功: {success_count} 篇")
    print(f"❌ 失败: {total_processed - success_count} 篇")
    print(f"🏷️  涉及分类: {', '.join(processed_categories)}")
    
    if success_count > 0:
        print("\n💾 新处理的论文已保存到数据库，网站将显示最新内容！")

if __name__ == "__main__":
    main() 