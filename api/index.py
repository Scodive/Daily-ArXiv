from http.server import BaseHTTPRequestHandler
import psycopg2
from datetime import datetime, timedelta
import json
import os
from urllib.parse import urlparse, parse_qs

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

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 解析URL路径
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        # 设置CORS头
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        
        try:
            if path == '/api/articles/recent':
                self.handle_recent_articles(query_params)
            elif path.startswith('/api/articles/') and path != '/api/articles/search':
                # 提取文章ID
                article_id = path.split('/')[-1]
                if article_id.isdigit():
                    self.handle_article_detail(int(article_id))
                else:
                    self.send_error_response(404, "论文不存在")
            elif path == '/api/articles/search':
                self.handle_search_articles(query_params)
            elif path == '/api/stats':
                self.handle_stats()
            else:
                self.send_error_response(404, "API端点不存在")
        except Exception as e:
            self.send_error_response(500, str(e))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_error_response(self, status_code, message):
        self.send_json_response({"error": message}, status_code)
    
    def get_param(self, query_params, key, default=None, param_type=str):
        """从查询参数中获取值"""
        if key in query_params and query_params[key]:
            try:
                return param_type(query_params[key][0])
            except (ValueError, TypeError):
                return default
        return default
    
    def handle_recent_articles(self, query_params):
        """获取最近一周的论文"""
        days = self.get_param(query_params, 'days', 7, int)
        limit = self.get_param(query_params, 'limit', 50, int)
        
        conn = connect_to_database()
        if not conn:
            self.send_error_response(500, "数据库连接失败")
            return
        
        cursor = conn.cursor()
        
        # 计算日期范围
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        query = """
            SELECT id, title, date_processed, tags, arxiv_id, pdf_url,
                   LEFT(content, 300) as content_preview
            FROM articles 
            WHERE date_processed >= %s AND date_processed <= %s
            ORDER BY date_processed DESC, id DESC 
            LIMIT %s;
        """
        
        cursor.execute(query, (start_date, end_date, limit))
        articles = cursor.fetchall()
        
        result = []
        for article in articles:
            result.append({
                "id": article[0],
                "title": article[1],
                "date_processed": article[2].strftime('%Y-%m-%d') if article[2] else None,
                "tags": article[3],
                "arxiv_id": article[4],
                "pdf_url": article[5],
                "content_preview": article[6] + "..." if article[6] else ""
            })
        
        cursor.close()
        conn.close()
        
        self.send_json_response({
            "success": True,
            "data": result,
            "total": len(result),
            "date_range": {
                "start": start_date.strftime('%Y-%m-%d'),
                "end": end_date.strftime('%Y-%m-%d')
            }
        })
    
    def handle_article_detail(self, article_id):
        """获取论文详细信息"""
        conn = connect_to_database()
        if not conn:
            self.send_error_response(500, "数据库连接失败")
            return
        
        cursor = conn.cursor()
        
        query = """
            SELECT id, title, content, date_processed, tags, arxiv_id, 
                   pdf_url, filename, created_at
            FROM articles 
            WHERE id = %s;
        """
        
        cursor.execute(query, (article_id,))
        article = cursor.fetchone()
        
        if not article:
            cursor.close()
            conn.close()
            self.send_error_response(404, "论文不存在")
            return
        
        result = {
            "id": article[0],
            "title": article[1],
            "content": article[2],
            "date_processed": article[3].strftime('%Y-%m-%d') if article[3] else None,
            "tags": article[4],
            "arxiv_id": article[5],
            "pdf_url": article[6],
            "filename": article[7],
            "created_at": article[8].strftime('%Y-%m-%d %H:%M:%S') if article[8] else None
        }
        
        cursor.close()
        conn.close()
        
        self.send_json_response({
            "success": True,
            "data": result
        })
    
    def handle_search_articles(self, query_params):
        """搜索论文"""
        keyword = self.get_param(query_params, 'keyword', '')
        limit = self.get_param(query_params, 'limit', 20, int)
        
        if not keyword:
            self.send_error_response(400, "请提供搜索关键词")
            return
        
        conn = connect_to_database()
        if not conn:
            self.send_error_response(500, "数据库连接失败")
            return
        
        cursor = conn.cursor()
        
        query = """
            SELECT id, title, date_processed, tags, arxiv_id,
                   LEFT(content, 200) as content_preview
            FROM articles 
            WHERE title ILIKE %s OR content ILIKE %s OR tags ILIKE %s
            ORDER BY date_processed DESC 
            LIMIT %s;
        """
        
        search_term = f'%{keyword}%'
        cursor.execute(query, (search_term, search_term, search_term, limit))
        articles = cursor.fetchall()
        
        result = []
        for article in articles:
            result.append({
                "id": article[0],
                "title": article[1],
                "date_processed": article[2].strftime('%Y-%m-%d') if article[2] else None,
                "tags": article[3],
                "arxiv_id": article[4],
                "content_preview": article[5] + "..." if article[5] else ""
            })
        
        cursor.close()
        conn.close()
        
        self.send_json_response({
            "success": True,
            "data": result,
            "total": len(result),
            "keyword": keyword
        })
    
    def handle_stats(self):
        """获取数据库统计信息"""
        conn = connect_to_database()
        if not conn:
            self.send_error_response(500, "数据库连接失败")
            return
        
        cursor = conn.cursor()
        
        # 总论文数
        cursor.execute("SELECT COUNT(*) FROM articles;")
        total_count = cursor.fetchone()[0]
        
        # 最近7天论文数
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE date_processed >= %s;
        """, (datetime.now().date() - timedelta(days=7),))
        recent_count = cursor.fetchone()[0]
        
        # 按日期统计
        cursor.execute("""
            SELECT date_processed, COUNT(*) 
            FROM articles 
            WHERE date_processed IS NOT NULL 
            GROUP BY date_processed 
            ORDER BY date_processed DESC 
            LIMIT 10;
        """)
        daily_stats = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        self.send_json_response({
            "success": True,
            "data": {
                "total_articles": total_count,
                "recent_articles": recent_count,
                "daily_stats": [
                    {
                        "date": stat[0].strftime('%Y-%m-%d'),
                        "count": stat[1]
                    } for stat in daily_stats
                ]
            }
        })

