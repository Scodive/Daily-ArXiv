import psycopg2
from datetime import datetime

def connect_to_database():
    """连接到PostgreSQL数据库"""
    try:
        conn = psycopg2.connect(
            host="dbprovider.ap-southeast-1.clawcloudrun.com",
            port=49674,
            database="postgres",
            user="postgres",
            password="sbdx497p",
            sslmode="prefer"
        )
        return conn
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

def show_table_info(conn):
    """显示表的基本信息"""
    cursor = conn.cursor()
    
    # 获取表结构
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default 
        FROM information_schema.columns 
        WHERE table_name = 'articles' 
        ORDER BY ordinal_position;
    """)
    
    columns = cursor.fetchall()
    print("📊 Articles表结构:")
    print("-" * 80)
    for col in columns:
        print(f"  {col[0]} ({col[1]}) - 可空: {col[2]} - 默认值: {col[3]}")
    print()

def show_statistics(conn):
    """显示统计信息"""
    cursor = conn.cursor()
    
    # 总数
    cursor.execute("SELECT COUNT(*) FROM articles;")
    total = cursor.fetchone()[0]
    print(f"📈 总论文数: {total}")
    
    # 按日期统计
    cursor.execute("""
        SELECT date_processed, COUNT(*) 
        FROM articles 
        WHERE date_processed IS NOT NULL 
        GROUP BY date_processed 
        ORDER BY date_processed DESC 
        LIMIT 10;
    """)
    
    date_stats = cursor.fetchall()
    print("\n📅 最近10天的论文数量:")
    for date, count in date_stats:
        print(f"  {date}: {count}篇")
    
    # 有ArXiv ID的论文数
    cursor.execute("SELECT COUNT(*) FROM articles WHERE arxiv_id IS NOT NULL;")
    arxiv_count = cursor.fetchone()[0]
    print(f"\n📄 有ArXiv ID的论文: {arxiv_count}篇")
    
    print()

def search_articles(conn, keyword=None, limit=10):
    """搜索论文"""
    cursor = conn.cursor()
    
    if keyword:
        query = """
            SELECT id, title, date_processed, tags 
            FROM articles 
            WHERE title ILIKE %s OR content ILIKE %s OR tags ILIKE %s
            ORDER BY date_processed DESC 
            LIMIT %s;
        """
        cursor.execute(query, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', limit))
        print(f"🔍 搜索关键词 '{keyword}' 的结果:")
    else:
        query = """
            SELECT id, title, date_processed, tags 
            FROM articles 
            ORDER BY date_processed DESC 
            LIMIT %s;
        """
        cursor.execute(query, (limit,))
        print(f"📝 最新 {limit} 篇论文:")
    
    articles = cursor.fetchall()
    print("-" * 120)
    
    for article in articles:
        id_num, title, date, tags = article
        date_str = date.strftime('%Y-%m-%d') if date else '未知日期'
        tags_str = tags if tags else '无标签'
        print(f"ID: {id_num:2d} | {date_str} | {title}")
        print(f"     标签: {tags_str}")
        print()

def get_article_content(conn, article_id):
    """获取指定文章的完整内容"""
    cursor = conn.cursor()
    
    query = """
        SELECT title, content, date_processed, tags, arxiv_id, pdf_url 
        FROM articles 
        WHERE id = %s;
    """
    
    cursor.execute(query, (article_id,))
    result = cursor.fetchone()
    
    if result:
        title, content, date, tags, arxiv_id, pdf_url = result
        print(f"📖 论文详情 (ID: {article_id})")
        print("=" * 100)
        print(f"标题: {title}")
        print(f"日期: {date.strftime('%Y-%m-%d') if date else '未知'}")
        print(f"标签: {tags if tags else '无'}")
        print(f"ArXiv ID: {arxiv_id if arxiv_id else '无'}")
        print(f"PDF链接: {pdf_url if pdf_url else '无'}")
        print("-" * 100)
        print("内容:")
        print(content)
        print("=" * 100)
    else:
        print(f"❌ 未找到ID为 {article_id} 的论文")

def main():
    conn = connect_to_database()
    if not conn:
        return
    
    try:
        while True:
            print("\n🤖 Daily-ArXiv 论文数据库查询系统")
            print("=" * 50)
            print("1. 显示表信息和统计")
            print("2. 查看最新论文")
            print("3. 搜索论文")
            print("4. 查看具体论文内容")
            print("5. 退出")
            print("-" * 50)
            
            choice = input("请选择操作 (1-5): ").strip()
            
            if choice == '1':
                show_table_info(conn)
                show_statistics(conn)
                
            elif choice == '2':
                try:
                    limit = int(input("显示多少篇最新论文? (默认10): ") or "10")
                    search_articles(conn, limit=limit)
                except ValueError:
                    search_articles(conn, limit=10)
                    
            elif choice == '3':
                keyword = input("请输入搜索关键词: ").strip()
                if keyword:
                    try:
                        limit = int(input("显示多少条结果? (默认10): ") or "10")
                        search_articles(conn, keyword, limit)
                    except ValueError:
                        search_articles(conn, keyword, 10)
                else:
                    print("❌ 请输入有效的关键词")
                    
            elif choice == '4':
                try:
                    article_id = int(input("请输入论文ID: "))
                    get_article_content(conn, article_id)
                except ValueError:
                    print("❌ 请输入有效的数字ID")
                    
            elif choice == '5':
                print("👋 再见！")
                break
                
            else:
                print("❌ 无效选择，请重试")
                
    except KeyboardInterrupt:
        print("\n👋 程序被用户中断，再见！")
    finally:
        conn.close()

if __name__ == "__main__":
    main() 