import psycopg2
import json
import os
from datetime import datetime
import re

def connect_to_database():
    """连接到PostgreSQL数据库"""
    try:
        # 尝试不同的连接参数
        conn = psycopg2.connect(
            host="dbprovider.ap-southeast-1.clawcloudrun.com",
            port=49674,
            database="postgres",
            user="postgres",
            password="sbdx497p",
            sslmode="prefer"
        )
        print("数据库连接成功！")
        return conn
    except Exception as e:
        print(f"数据库连接失败: {e}")
        print("请检查以下连接信息:")
        print("- 主机: dbprovider.ap-southeast-1.clawcloudrun.com")
        print("- 端口: 49674")
        print("- 数据库: postgres") 
        print("- 用户名: postgres")
        print("- 密码: sbdx497p")
        return None

def create_articles_table(conn):
    """创建论文表"""
    cursor = conn.cursor()
    
    # 删除表如果存在
    cursor.execute("DROP TABLE IF EXISTS articles CASCADE;")
    
    # 创建论文表
    create_table_sql = """
    CREATE TABLE articles (
        id SERIAL PRIMARY KEY,
        title VARCHAR(500) NOT NULL,
        arxiv_id VARCHAR(50),
        pdf_url TEXT,
        filename VARCHAR(300) NOT NULL,
        date_processed DATE,
        tags TEXT,
        content TEXT NOT NULL,
        image_dir VARCHAR(300),
        first_page_image VARCHAR(300),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    cursor.execute(create_table_sql)
    conn.commit()
    print("成功创建articles表")

def extract_content_parts(content):
    """从论文内容中提取标题和正文"""
    lines = content.strip().split('\n')
    
    # 提取标题（第一行以"标题："开头）
    title = ""
    content_lines = []
    
    for i, line in enumerate(lines):
        if line.startswith("标题："):
            title = line.replace("标题：", "").strip()
        elif line.strip() and not line.startswith("标题："):
            content_lines.append(line)
    
    # 提取标签（最后一行以"标签："开头）
    tags = ""
    if content_lines and content_lines[-1].startswith("标签："):
        tags = content_lines[-1].replace("标签：", "").strip()
        content_lines = content_lines[:-1]
    
    main_content = '\n'.join(content_lines).strip()
    
    return title, main_content, tags

def parse_filename_date(filename):
    """从文件名中提取日期"""
    # 文件名格式：2025-06-09_论文标题.txt
    match = re.match(r'(\d{4}-\d{2}-\d{2})_', filename)
    if match:
        try:
            return datetime.strptime(match.group(1), '%Y-%m-%d').date()
        except:
            return None
    return None

def load_articles_index(base_path):
    """加载articles_index.json文件"""
    index_path = os.path.join(base_path, "articles_index.json")
    if os.path.exists(index_path):
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"读取articles_index.json失败: {e}")
    return []

def insert_articles(conn, base_path):
    """插入所有论文到数据库"""
    cursor = conn.cursor()
    
    # 加载索引文件
    articles_index = load_articles_index(base_path)
    index_dict = {item['txt_filename']: item for item in articles_index}
    
    # 获取所有txt文件
    txt_files = [f for f in os.listdir(base_path) if f.endswith('.txt')]
    
    inserted_count = 0
    
    for filename in txt_files:
        try:
            filepath = os.path.join(base_path, filename)
            
            # 读取文件内容
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取内容部分
            title, main_content, tags = extract_content_parts(content)
            
            # 从索引中获取额外信息
            index_info = index_dict.get(filename, {})
            arxiv_id = index_info.get('arxiv_id')
            pdf_url = index_info.get('pdf_url')
            image_dir = index_info.get('image_dir')
            first_page_image = index_info.get('first_page_image')
            
            # 解析日期
            date_processed = parse_filename_date(filename)
            if not date_processed and 'date_processed' in index_info:
                try:
                    date_processed = datetime.strptime(index_info['date_processed'], '%Y-%m-%d').date()
                except:
                    pass
            
            # 如果从内容中没有提取到标题，使用文件名
            if not title:
                # 从文件名中提取标题（去掉日期前缀和.txt后缀）
                title_match = re.match(r'\d{4}-\d{2}-\d{2}_(.+)\.txt', filename)
                if title_match:
                    title = title_match.group(1)
                else:
                    title = filename.replace('.txt', '')
            
            # 插入数据库
            insert_sql = """
            INSERT INTO articles (title, arxiv_id, pdf_url, filename, date_processed, 
                                tags, content, image_dir, first_page_image)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_sql, (
                title,
                arxiv_id,
                pdf_url,
                filename,
                date_processed,
                tags,
                main_content,
                image_dir,
                first_page_image
            ))
            
            inserted_count += 1
            print(f"成功插入: {title}")
            
        except Exception as e:
            print(f"插入文件 {filename} 失败: {e}")
            continue
    
    conn.commit()
    print(f"总共成功插入 {inserted_count} 篇论文")

def main():
    # 连接数据库
    conn = connect_to_database()
    if not conn:
        return
    
    try:
        # 创建表
        create_articles_table(conn)
        
        # 插入数据
        base_path = "/Users/sco/Desktop/Daily-ArXiv/generated_articles"
        insert_articles(conn, base_path)
        
        # 验证插入结果
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles;")
        count = cursor.fetchone()[0]
        print(f"数据库中共有 {count} 篇论文")
        
        # 显示最近几篇文章
        cursor.execute("SELECT title, date_processed FROM articles ORDER BY date_processed DESC LIMIT 5;")
        recent_articles = cursor.fetchall()
        print("\n最近的5篇论文:")
        for title, date in recent_articles:
            print(f"- {date}: {title}")
            
    except Exception as e:
        print(f"操作失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main() 