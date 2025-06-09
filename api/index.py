from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)
CORS(app)  # 允许跨域请求

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

@app.route('/api/articles/recent', methods=['GET'])
def get_recent_articles():
    """获取最近一周的论文"""
    try:
        days = request.args.get('days', 7, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        conn = connect_to_database()
        if not conn:
            return jsonify({"error": "数据库连接失败"}), 500
        
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
        
        return jsonify({
            "success": True,
            "data": result,
            "total": len(result),
            "date_range": {
                "start": start_date.strftime('%Y-%m-%d'),
                "end": end_date.strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/articles/<int:article_id>', methods=['GET'])
def get_article_detail(article_id):
    """获取论文详细信息"""
    try:
        conn = connect_to_database()
        if not conn:
            return jsonify({"error": "数据库连接失败"}), 500
        
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
            return jsonify({"error": "论文不存在"}), 404
        
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
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/articles/search', methods=['GET'])
def search_articles():
    """搜索论文"""
    try:
        keyword = request.args.get('keyword', '')
        limit = request.args.get('limit', 20, type=int)
        
        if not keyword:
            return jsonify({"error": "请提供搜索关键词"}), 400
        
        conn = connect_to_database()
        if not conn:
            return jsonify({"error": "数据库连接失败"}), 500
        
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
        
        return jsonify({
            "success": True,
            "data": result,
            "total": len(result),
            "keyword": keyword
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取数据库统计信息"""
    try:
        conn = connect_to_database()
        if not conn:
            return jsonify({"error": "数据库连接失败"}), 500
        
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
        
        return jsonify({
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
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Vercel需要的handler函数
def handler(request):
    return app(request.environ, request.start_response)

# 对于Vercel，我们需要这个
app.wsgi_app = handler

# 如果直接运行，用于本地测试
if __name__ == '__main__':
    app.run(debug=True)