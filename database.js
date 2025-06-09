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
    
    // 清理标签字符串
    const cleanTags = tagsString.replace(/^标签：\s*/, '').trim();
    if (!cleanTags) return '';
    
    // 按#分割并清理，生成HTML标签
    return cleanTags.split('#').filter(tag => tag.trim()).map(tag => 
        `<span class="paper-tag">#${tag.trim()}</span>`
    ).join('');
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
    
    // 创建内容预览（前150字符）
    const contentPreview = article.content ? 
        article.content.substring(0, 150).replace(/标题：.*?\n\n?/, '') + '...' : 
        '暂无预览内容';
    
    return `
        <div class="paper-card" onclick="showArticleDetail(${article.id})">
            <div class="paper-card-header">
                <h3 class="paper-title">${article.title}</h3>
                <div class="paper-meta">
                    <span class="date"><i class="fas fa-calendar"></i> ${formatDate(article.date_processed)}</span>
                    ${article.arxiv_id ? `<span class="arxiv"><i class="fas fa-link"></i> ${article.arxiv_id}</span>` : ''}
                </div>
                <div class="paper-tags">
                    ${tags}
                </div>
            </div>
            <div class="paper-content">
                <div class="paper-preview">
                    ${contentPreview}
                </div>
                <div class="paper-actions">
                    <button class="paper-btn primary" onclick="event.stopPropagation(); showArticleDetail(${article.id})">
                        <i class="fas fa-eye"></i>
                        <span>查看解读</span>
                    </button>
                    ${article.pdf_url ? `
                        <a href="${article.pdf_url}" target="_blank" onclick="event.stopPropagation()" class="paper-btn">
                            <i class="fas fa-file-pdf"></i>
                            <span>原文PDF</span>
                        </a>
                    ` : ''}
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
    // 获取今日论文容器
    const dailyContainer = document.getElementById('daily-papers-grid');
    // 获取历史论文容器
    const archiveContainer = document.getElementById('archive-papers-grid');
    
    if (!dailyContainer && !archiveContainer) {
        console.error('未找到论文展示容器');
        return;
    }
    
    // 显示今日论文（最近1天）
    if (dailyContainer) {
        dailyContainer.innerHTML = '<div class="loading-articles"><div class="spinner"></div><p>正在加载今日论文...</p></div>';
        
        fetchRecentArticles(1)
            .then(articles => {
                if (articles.length > 0) {
                    displayArticles(articles, dailyContainer, 'daily');
                } else {
                    dailyContainer.innerHTML = '<div class="no-articles">今日暂无新论文</div>';
                }
            })
            .catch(error => {
                dailyContainer.innerHTML = `
                    <div class="error-message">
                        <p>加载今日论文失败: ${error.message}</p>
                        <button onclick="initArticleDisplay()" class="button">重试</button>
                    </div>
                `;
            });
    }
    
    // 显示历史论文（最近30天，排除今天）
    if (archiveContainer) {
        archiveContainer.innerHTML = '<div class="loading-articles"><div class="spinner"></div><p>正在加载历史论文...</p></div>';
        
        fetchRecentArticles(30)
            .then(articles => {
                // 过滤掉今日的论文，只显示历史论文
                const today = new Date().toDateString();
                const historicalArticles = articles.filter(article => {
                    const articleDate = new Date(article.date_processed).toDateString();
                    return articleDate !== today;
                });
                
                if (historicalArticles.length > 0) {
                    displayArticles(historicalArticles.slice(0, 6), archiveContainer, 'archive');
                } else {
                    archiveContainer.innerHTML = '<div class="no-articles">暂无历史论文</div>';
                }
            })
            .catch(error => {
                archiveContainer.innerHTML = `
                    <div class="error-message">
                        <p>加载历史论文失败: ${error.message}</p>
                        <button onclick="initArticleDisplay()" class="button">重试</button>
                    </div>
                `;
            });
    }
}

// 初始化搜索功能
function initSearchFeature() {
    // 绑定档案区搜索
    const archiveSearchInput = document.getElementById('archive-search');
    const dateFilter = document.getElementById('date-filter');
    
    if (archiveSearchInput) {
        archiveSearchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                performArchiveSearch();
            }
        });
    }
    
    if (dateFilter) {
        dateFilter.addEventListener('change', performArchiveSearch);
    }
}

// 执行档案区搜索
function performArchiveSearch() {
    const searchInput = document.getElementById('archive-search');
    const dateFilter = document.getElementById('date-filter');
    const keyword = searchInput ? searchInput.value.trim() : '';
    const timeFilter = dateFilter ? dateFilter.value : 'all';
    
    const container = document.getElementById('archive-papers-grid');
    if (!container) return;
    
    container.innerHTML = '<div class="loading-articles"><div class="spinner"></div><p>正在搜索...</p></div>';
    
    // 根据时间过滤确定搜索天数
    let searchDays = 365; // 默认一年
    switch(timeFilter) {
        case 'week': searchDays = 7; break;
        case 'month': searchDays = 30; break;
        case 'quarter': searchDays = 90; break;
    }
    
    if (keyword) {
        // 如果有关键词，进行搜索
        searchArticles(keyword)
            .then(articles => {
                // 按时间过滤
                const filteredArticles = filterArticlesByTime(articles, searchDays);
                displayArticles(filteredArticles, container);
            })
            .catch(error => {
                container.innerHTML = `
                    <div class="error-message">
                        <p>搜索失败: ${error.message}</p>
                        <button onclick="loadArchiveArticles()" class="button">重新加载</button>
                    </div>
                `;
            });
    } else {
        // 如果没有关键词，只按时间过滤
        fetchRecentArticles(searchDays)
            .then(articles => {
                // 过滤掉今日的论文
                const today = new Date().toDateString();
                const historicalArticles = articles.filter(article => {
                    const articleDate = new Date(article.date_processed).toDateString();
                    return articleDate !== today;
                });
                
                displayArticles(historicalArticles, container);
            })
            .catch(error => {
                container.innerHTML = `
                    <div class="error-message">
                        <p>加载失败: ${error.message}</p>
                        <button onclick="loadArchiveArticles()" class="button">重新加载</button>
                    </div>
                `;
            });
    }
}

// 按时间过滤文章
function filterArticlesByTime(articles, days) {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);
    
    return articles.filter(article => {
        const articleDate = new Date(article.date_processed);
        return articleDate >= cutoffDate;
    });
}

// 加载档案文章
function loadArchiveArticles() {
    const archiveContainer = document.getElementById('archive-papers-grid');
    if (!archiveContainer) return;
    
    archiveContainer.innerHTML = '<div class="loading-articles"><div class="spinner"></div><p>正在加载历史论文...</p></div>';
    
    fetchRecentArticles(30)
        .then(articles => {
            const today = new Date().toDateString();
            const historicalArticles = articles.filter(article => {
                const articleDate = new Date(article.date_processed).toDateString();
                return articleDate !== today;
            });
            
            if (historicalArticles.length > 0) {
                displayArticles(historicalArticles.slice(0, 6), archiveContainer);
            } else {
                archiveContainer.innerHTML = '<div class="no-articles">暂无历史论文</div>';
            }
        })
        .catch(error => {
            archiveContainer.innerHTML = `
                <div class="error-message">
                    <p>加载历史论文失败: ${error.message}</p>
                    <button onclick="loadArchiveArticles()" class="button">重试</button>
                </div>
            `;
        });
}

// 加载更多文章
function loadMoreArticles() {
    const container = document.getElementById('archive-papers-grid');
    const loadMoreBtn = document.getElementById('load-more-btn');
    
    if (!container || !loadMoreBtn) return;
    
    loadMoreBtn.innerHTML = '<div class="spinner"></div><span>加载中...</span>';
    loadMoreBtn.disabled = true;
    
    // 这里可以实现分页加载逻辑
    // 暂时重新加载更多文章
    fetchRecentArticles(60)
        .then(articles => {
            const today = new Date().toDateString();
            const historicalArticles = articles.filter(article => {
                const articleDate = new Date(article.date_processed).toDateString();
                return articleDate !== today;
            });
            
            displayArticles(historicalArticles, container);
            
            loadMoreBtn.innerHTML = '<span>加载更多</span><i class="fas fa-chevron-down"></i>';
            loadMoreBtn.disabled = false;
            
            // 如果文章数量少于预期，隐藏加载更多按钮
            if (historicalArticles.length < 20) {
                loadMoreBtn.style.display = 'none';
            }
        })
        .catch(error => {
            loadMoreBtn.innerHTML = '<span>加载失败，点击重试</span><i class="fas fa-exclamation-triangle"></i>';
            loadMoreBtn.disabled = false;
        });
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    initSearchFeature();
    initArticleDisplay();
}); 