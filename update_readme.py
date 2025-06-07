import os
import re
from datetime import datetime

def get_article_files():
    articles_dir = "generated_articles"
    articles = []
    
    # 遍历生成的文章目录
    for filename in os.listdir(articles_dir):
        if filename.endswith('.txt'):
            # 解析文件名中的日期和标题
            match = re.match(r'(\d{4}-\d{2}-\d{2})_(.*?)\.txt$', filename)
            if match:
                date_str, title = match.groups()
                date = datetime.strptime(date_str, '%Y-%m-%d')
                articles.append({
                    'date': date,
                    'title': title,
                    'filename': filename
                })
    
    # 按日期降序排序
    return sorted(articles, key=lambda x: x['date'], reverse=True)

def update_readme():
    # 读取现有的README内容
    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 获取所有文章
    articles = get_article_files()
    
    # 生成新的Latest Papers部分
    latest_papers = "## Latest arXiv Papers\n\n"
    for article in articles:
        article_link = f"generated_articles/{article['filename']}"
        latest_papers += f"- {article['date'].strftime('%Y-%m-%d')} [{article['title']}]({article_link})\n"
    
    latest_papers += "\n"
    
    # 检查是否已经存在Latest Papers部分
    if "## Latest arXiv Papers" in content:
        # 如果存在，替换整个部分
        pattern = r"## Latest arXiv Papers\n\n(?:.*?\n)*?\n"
        content = re.sub(pattern, latest_papers, content, flags=re.DOTALL)
    else:
        # 如果不存在，在文件开头添加
        content = latest_papers + content
    
    # 保存更新后的README
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    update_readme() 