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
        console.log(`正在获取最近${days}天的论文...`);
        const url = `${API_BASE_URL}/articles/recent?days=${days}&limit=20`;
        console.log('API URL:', url);
        
        const response = await fetch(url);
        console.log('API响应状态:', response.status);
        
        // 如果API失败，返回空数组
        if (!response.ok) {
            console.warn('API失败');
            return [];
        }
        
        const data = await response.json();
        console.log('API响应数据:', data);
        
        if (data.success) {
            console.log(`成功获取${data.data.length}篇论文`);
            return data.data;
        } else {
            throw new Error(data.error || '获取数据失败');
        }
    } catch (error) {
        console.error('获取论文数据失败:', error);
        return [];
    }
}

// 获取指定日期的论文
async function fetchArticlesByDate(date) {
    try {
        const url = `${API_BASE_URL}/articles/by-date?date=${date}&limit=20`;
        console.log('按日期获取论文 URL:', url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            return [];
        }
        
        const data = await response.json();
        
        if (data.success) {
            return data.data;
        } else {
            return [];
        }
    } catch (error) {
        console.error('按日期获取论文失败:', error);
        return [];
    }
}

// 智能获取今日论文（如果今日没有则往前查找）
async function fetchTodayArticles() {
    const today = new Date();
    
    // 从今天开始，往前查找最多7天
    for (let i = 0; i < 7; i++) {
        const checkDate = new Date(today);
        checkDate.setDate(today.getDate() - i);
        const dateString = checkDate.toISOString().split('T')[0];
        
        console.log(`检查日期 ${dateString} 的论文...`);
        
        const articles = await fetchArticlesByDate(dateString);
        
        if (articles && articles.length > 0) {
            console.log(`在 ${dateString} 找到 ${articles.length} 篇论文`);
            return {
                articles: articles,
                date: dateString,
                isToday: i === 0
            };
        }
    }
    
    console.log('最近7天都没有找到论文');
    return {
        articles: [],
        date: null,
        isToday: false
    };
}

// 模拟数据函数
function getMockArticles() {
    const today = new Date().toISOString().split('T')[0];
    const yesterday = new Date(Date.now() - 24*60*60*1000).toISOString().split('T')[0];
    
    return [
        {
            id: 1,
            title: "SPEC：港中文提出可解释的特征嵌入比较与对齐框架",
            content: "式捕获的样本聚类。具体来说，该方法计算两个嵌入的差异，并分析差异核距阵的主要特征向量，以解释聚类分配的差异。为了解决大规模数据集上的计算挑战，研究者们开发了一种可扩展的SPEC实现，其计算复杂度随样本大小线性增长。此外，他们还引入了一个优化问题，利用该框架对齐两个嵌入，确保在一个嵌入中识别的聚类也能在另一个模型中被捕获。该方法还利用随机傅里叶特征（RFF）来处理移位不变核函数（如高斯核）的计算，进一步提高了效率。",
            tags: "#特征嵌入 #可解释性 #聚类 #模型对齐 #机器学习",
            arxiv_id: "2506.06231",
            pdf_url: "https://arxiv.org/pdf/2506.06231.pdf",
            date_processed: today
        },
        {
            id: 2,
            title: "AdaCM2：自适应跨模态记忆缓存，解锁超长视频理解新姿势",
            content: "AdaCM2框架为解决超长视频理解中的记忆限制问题提供了创新解决方案。该方法通过自适应跨模态记忆缓存机制，有效管理视频序列中的关键信息，支持对长达数小时视频内容的深度理解。研究团队设计了智能的记忆分配策略，确保重要的视觉和语义信息得到优先保留，同时动态调整缓存容量以适应不同长度的视频内容。",
            tags: "#长视频理解 #跨模态学习 #自适应记忆 #人工智能 #视频分析",
            arxiv_id: "2506.06232",
            pdf_url: "https://arxiv.org/pdf/2506.06232.pdf",
            date_processed: today
        },
        {
            id: 3,
            title: "Transformer架构的记忆优化：解决长序列建模挑战",
            content: "研究团队提出了一种新颖的Transformer记忆优化策略，通过分层注意力机制和动态上下文压缩技术，显著提升了长序列处理效率。该方法在保持模型性能的同时，将内存使用量降低了60%以上，为处理超长文档和多轮对话提供了实用解决方案。",
            tags: "#Transformer #记忆优化 #长序列建模 #注意力机制 #深度学习",
            arxiv_id: "2506.06233",
            pdf_url: "https://arxiv.org/pdf/2506.06233.pdf",
            date_processed: yesterday
        },
        {
            id: 4,
            title: "量子增强机器学习：QAOA算法在组合优化中的新突破",
            content: "本研究展示了量子近似优化算法(QAOA)在解决复杂组合优化问题中的显著优势。通过改进的量子线路设计和噪声缓解技术，该方法在图着色、最大割等NP-hard问题上达到了超越经典算法的性能表现。",
            tags: "#量子计算 #机器学习 #组合优化 #QAOA #量子算法",
            arxiv_id: "2506.06234",
            pdf_url: "https://arxiv.org/pdf/2506.06234.pdf",
            date_processed: yesterday
        }
    ];
}

// 获取论文详情
async function fetchArticleDetail(articleId) {
    try {
        const response = await fetch(`${API_BASE_URL}/articles/${articleId}`);
        
        if (!response.ok) {
            throw new Error('论文不存在');
        }
        
        const data = await response.json();
        
        if (data.success) {
            return data.data;
        } else {
            throw new Error(data.error || '获取论文详情失败');
        }
    } catch (error) {
        console.error('获取论文详情失败:', error);
        throw new Error('无法获取论文详情');
    }
}

// 搜索论文
async function searchArticles(keyword) {
    try {
        const response = await fetch(`${API_BASE_URL}/articles/search?keyword=${encodeURIComponent(keyword)}&limit=20`);
        
        if (!response.ok) {
            return [];
        }
        
        const data = await response.json();
        
        if (data.success) {
            return data.data;
        } else {
            throw new Error(data.error || '搜索失败');
        }
    } catch (error) {
        console.error('搜索失败:', error);
        return [];
    }
}

// 创建论文卡片HTML
function createArticleCard(article) {
    const tags = formatTags(article.tags);
    
    // 创建内容预览
    let contentPreview = '暂无预览内容';
    
    if (article.content && typeof article.content === 'string' && article.content.trim().length > 0) {
        let cleanContent = article.content;
        
        // 移除标题行（如果存在）
        cleanContent = cleanContent.replace(/^标题：.*?\n+/g, '');
        
        // 移除标签行（如果在末尾）
        cleanContent = cleanContent.replace(/\n+标签：.*?$/g, '');
        
        // 移除多余的换行和空白
        cleanContent = cleanContent.trim();
        
        // 如果清理后还有内容，创建预览
        if (cleanContent.length > 0) {
            // 取前150个字符
            contentPreview = cleanContent.length > 150 ? 
                cleanContent.substring(0, 150) + '...' : 
                cleanContent;
        }
    }
    
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
    
    // 调试：输出文章数据结构
    console.log('文章数据:', articles);
    console.log('第一篇文章:', articles[0]);
    
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
    
    // 禁止背景滚动
    document.body.classList.add('modal-open');
    
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
    
    // 添加ESC键关闭功能
    const handleEscape = (e) => {
        if (e.key === 'Escape') {
            closeModal();
        }
    };
    document.addEventListener('keydown', handleEscape);
    
    // 防止移动设备滚动穿透
    const handleTouchMove = (e) => {
        // 如果事件目标不在模态框内容区域内，阻止默认行为
        const modalBody = modal.querySelector('.modal-body');
        if (!modalBody.contains(e.target)) {
            e.preventDefault();
        }
    };
    document.addEventListener('touchmove', handleTouchMove, { passive: false });
    
    // 将事件处理器存储到模态框元素上，以便清理
    modal._escapeHandler = handleEscape;
    modal._touchMoveHandler = handleTouchMove;
}

// 关闭模态框
function closeModal() {
    const modal = document.getElementById('article-modal');
    if (modal) {
        // 清理ESC键事件监听器
        if (modal._escapeHandler) {
            document.removeEventListener('keydown', modal._escapeHandler);
        }
        
        // 清理触摸事件监听器
        if (modal._touchMoveHandler) {
            document.removeEventListener('touchmove', modal._touchMoveHandler);
        }
        
        // 移除模态框
        modal.remove();
        
        // 恢复背景滚动
        document.body.classList.remove('modal-open');
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
    
    // 显示今日论文（智能查找最新有数据的日期）
    if (dailyContainer) {
        dailyContainer.innerHTML = '<div class="loading-articles"><div class="spinner"></div><p>正在加载今日论文...</p></div>';
        
        fetchTodayArticles()
            .then(result => {
                if (result.articles.length > 0) {
                    // 按日期排序，最新的在前，最多显示4篇
                    const sortedArticles = result.articles.sort((a, b) => new Date(b.date_processed) - new Date(a.date_processed));
                    const displayArticles_limited = sortedArticles.slice(0, 4);
                    displayArticles(displayArticles_limited, dailyContainer, 'daily');
                    
                    // 更新页面顶部的日期显示
                    const dateElement = document.getElementById('today-date');
                    if (dateElement && result.date) {
                        const displayDate = new Date(result.date);
                        const dateText = displayDate.toLocaleDateString('zh-CN', {
                            month: 'long',
                            day: 'numeric'
                        });
                        
                        if (result.isToday) {
                            dateElement.textContent = dateText;
                            dateElement.className = 'date-badge';
                        } else {
                            dateElement.textContent = dateText + ' (最新)';
                            dateElement.className = 'date-badge latest';
                        }
                    }
                } else {
                    dailyContainer.innerHTML = '<div class="no-articles">暂无最新论文</div>';
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
    // 清理可能残留的模态框状态
    document.body.classList.remove('modal-open');
    
    initSearchFeature();
    initArticleDisplay();
}); 