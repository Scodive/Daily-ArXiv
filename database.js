// 数据库API基础URL
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:5001/api' 
    : '/api';

// 格式化日期
function formatDate(dateString) {
    if (!dateString) return '未知日期';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// 格式化标签
function formatTags(tagsString) {
    if (!tagsString) return '';
    return tagsString.split(' ').map(tag => 
        tag.trim().startsWith('#') ? tag.trim() : '#' + tag.trim()
    ).join(' ');
}

// 获取最近的论文
async function fetchRecentArticles(days = 7) {
    try {
        const response = await fetch(`${API_BASE_URL}/articles/recent?days=${days}&limit=20`);
        const data = await response.json();
        
        if (data.success) {
            return data.data;
        } else {
            throw new Error(data.error || '获取数据失败');
        }
    } catch (error) {
        console.error('获取论文数据失败:', error);
        throw error;
    }
}

// 获取论文详情
async function fetchArticleDetail(articleId) {
    try {
        const response = await fetch(`${API_BASE_URL}/articles/${articleId}`);
        const data = await response.json();
        
        if (data.success) {
            return data.data;
        } else {
            throw new Error(data.error || '获取论文详情失败');
        }
    } catch (error) {
        console.error('获取论文详情失败:', error);
        throw error;
    }
}

// 搜索论文
async function searchArticles(keyword) {
    try {
        const response = await fetch(`${API_BASE_URL}/articles/search?keyword=${encodeURIComponent(keyword)}&limit=20`);
        const data = await response.json();
        
        if (data.success) {
            return data.data;
        } else {
            throw new Error(data.error || '搜索失败');
        }
    } catch (error) {
        console.error('搜索失败:', error);
        throw error;
    }
}

// 创建论文卡片HTML
function createArticleCard(article) {
    const tags = formatTags(article.tags);
    
    return `
        <div class="article-card" onclick="showArticleDetail(${article.id})">
            <div class="article-header">
                <h3 class="article-title">${article.title}</h3>
                <span class="article-date">${formatDate(article.date_processed)}</span>
            </div>
            <div class="article-preview">
                ${article.content_preview || '暂无预览内容'}
            </div>
            <div class="article-footer">
                <div class="article-tags">${tags}</div>
                <div class="article-links">
                    ${article.arxiv_id ? `<span class="arxiv-id">ArXiv: ${article.arxiv_id}</span>` : ''}
                    ${article.pdf_url ? `<a href="${article.pdf_url}" target="_blank" onclick="event.stopPropagation()" class="pdf-link">📄 PDF</a>` : ''}
                </div>
            </div>
        </div>
    `;
}

// 显示论文列表
function displayArticles(articles, container) {
    if (!articles || articles.length === 0) {
        container.innerHTML = '<div class="no-articles">暂无论文数据</div>';
        return;
    }
    
    const articlesHTML = articles.map(article => createArticleCard(article)).join('');
    container.innerHTML = articlesHTML;
}

// 显示论文详情模态框
function showArticleDetail(articleId) {
    // 创建加载状态
    showModal('正在加载论文详情...', true);
    
    // 获取论文详情
    fetchArticleDetail(articleId)
        .then(article => {
            const modalContent = createArticleDetailHTML(article);
            showModal(modalContent, false);
        })
        .catch(error => {
            showModal(`加载失败: ${error.message}`, false);
        });
}

// 创建论文详情HTML
function createArticleDetailHTML(article) {
    const tags = formatTags(article.tags);
    
    return `
        <div class="article-detail">
            <div class="article-detail-header">
                <h2>${article.title}</h2>
                <div class="article-meta">
                    <span class="date">📅 ${formatDate(article.date_processed)}</span>
                    ${article.arxiv_id ? `<span class="arxiv">🔗 ArXiv: ${article.arxiv_id}</span>` : ''}
                </div>
                <div class="article-tags">${tags}</div>
            </div>
            
            <div class="article-content">
                <pre>${article.content}</pre>
            </div>
            
            <div class="article-actions">
                ${article.pdf_url ? `<a href="${article.pdf_url}" target="_blank" class="button">📄 查看原文PDF</a>` : ''}
                <button onclick="downloadArticleText(${article.id}, '${article.title}')" class="button">💾 下载解读文本</button>
            </div>
        </div>
    `;
}

// 显示模态框
function showModal(content, isLoading = false) {
    // 移除现有模态框
    const existingModal = document.getElementById('article-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 创建新模态框
    const modal = document.createElement('div');
    modal.id = 'article-modal';
    modal.className = 'modal';
    
    modal.innerHTML = `
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal()">&times;</span>
            <div class="modal-body ${isLoading ? 'loading' : ''}">
                ${isLoading ? '<div class="spinner"></div>' : ''}
                ${content}
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 添加点击外部关闭功能
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });
}

// 关闭模态框
function closeModal() {
    const modal = document.getElementById('article-modal');
    if (modal) {
        modal.remove();
    }
}

// 下载论文文本
async function downloadArticleText(articleId, title) {
    try {
        const article = await fetchArticleDetail(articleId);
        
        const content = `标题：${article.title}\n\n${article.content}`;
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `${title}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (error) {
        alert('下载失败: ' + error.message);
    }
}

// 初始化论文展示
function initArticleDisplay() {
    const container = document.getElementById('recommendation-cards');
    
    if (!container) {
        console.error('未找到论文展示容器');
        return;
    }
    
    // 显示加载状态
    container.innerHTML = '<div class="loading-articles"><div class="spinner"></div><p>正在加载最近的论文...</p></div>';
    
    // 获取并显示最近的论文
    fetchRecentArticles(7)
        .then(articles => {
            displayArticles(articles, container);
        })
        .catch(error => {
            container.innerHTML = `
                <div class="error-message">
                    <p>加载论文失败: ${error.message}</p>
                    <button onclick="initArticleDisplay()" class="button">重试</button>
                </div>
            `;
        });
}

// 添加搜索功能
function initSearchFeature() {
    // 创建搜索界面
    const searchHTML = `
        <div class="search-section">
            <div class="search-container">
                <input type="text" id="article-search" placeholder="搜索论文标题、内容或标签..." />
                <button onclick="performSearch()" class="button">搜索</button>
            </div>
        </div>
    `;
    
    // 在推荐部分之前插入搜索
    const recommendationSection = document.getElementById('recommendations');
    if (recommendationSection) {
        recommendationSection.insertAdjacentHTML('beforebegin', searchHTML);
        
        // 添加回车搜索功能
        const searchInput = document.getElementById('article-search');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    performSearch();
                }
            });
        }
    }
}

// 执行搜索
function performSearch() {
    const searchInput = document.getElementById('article-search');
    const keyword = searchInput.value.trim();
    
    if (!keyword) {
        alert('请输入搜索关键词');
        return;
    }
    
    const container = document.getElementById('recommendation-cards');
    container.innerHTML = '<div class="loading-articles"><div class="spinner"></div><p>正在搜索...</p></div>';
    
    searchArticles(keyword)
        .then(articles => {
            // 更新标题
            const recommendationTitle = document.querySelector('#recommendations h2');
            if (recommendationTitle) {
                recommendationTitle.textContent = `搜索结果: "${keyword}" (${articles.length}篇)`;
            }
            
            displayArticles(articles, container);
            
            // 添加返回按钮
            if (articles.length > 0) {
                container.insertAdjacentHTML('afterend', 
                    '<div class="search-actions"><button onclick="showRecentArticles()" class="button">返回最近论文</button></div>'
                );
            }
        })
        .catch(error => {
            container.innerHTML = `
                <div class="error-message">
                    <p>搜索失败: ${error.message}</p>
                    <button onclick="showRecentArticles()" class="button">返回最近论文</button>
                </div>
            `;
        });
}

// 显示最近论文
function showRecentArticles() {
    // 恢复标题
    const recommendationTitle = document.querySelector('#recommendations h2');
    if (recommendationTitle) {
        recommendationTitle.textContent = '近期解读推荐';
    }
    
    // 移除搜索操作按钮
    const searchActions = document.querySelector('.search-actions');
    if (searchActions) {
        searchActions.remove();
    }
    
    // 重新加载最近论文
    initArticleDisplay();
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    initSearchFeature();
    initArticleDisplay();
}); 