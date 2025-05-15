const GEMINI_API_KEY = 'AIzaSyDy9pYAEW7e2Ewk__9TCHAD5X_G1VhCtVw'; 
const GEMINI_API_URL = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=${GEMINI_API_KEY}`;


document.addEventListener('DOMContentLoaded', () => {
    const arxivUrlInput = document.getElementById('arxiv-url');
    const processButton = document.getElementById('process-button');
    const statusMessage = document.getElementById('status-message');
    const outputSection = document.getElementById('output-section');
    const outputTitle = document.getElementById('output-title');
    const outputContent = document.getElementById('output-content');
    const downloadTxtButton = document.getElementById('download-txt-button');
    const downloadPdfButton = document.getElementById('download-pdf-button');
    const spinnerWrapper = document.querySelector('.spinner-wrapper'); // Get the spinner wrapper

    let originalPdfBlob = null;
    let originalPdfName = 'original_paper.pdf';
    let generatedArticleTitle = 'AI解读文章';
    let generatedArticleFullContent = ''; // Store full content with title and tags

    processButton.addEventListener('click', async () => {
        const pdfUrl = arxivUrlInput.value.trim();
        if (!pdfUrl || !pdfUrl.toLowerCase().startsWith('https://arxiv.org/pdf/')) {
            showError('请输入有效的ArXiv PDF链接 (例如 https://arxiv.org/pdf/xxxx.xxxxx.pdf)');
            return;
        }

        // Derive PDF name from URL for download
        try {
            const urlParts = pdfUrl.split('/');
            let potentialName = urlParts[urlParts.length - 1];
            if (!potentialName.toLowerCase().endsWith('.pdf')) {
                potentialName += '.pdf';
            }
            originalPdfName = potentialName;
        } catch (e) { 
            console.warn("Could not derive PDF name from URL, using default.");
        }

        showLoading('正在处理论文...');
        outputSection.style.display = 'none';
        processButton.disabled = true;

        try {
            showLoading('步骤1/3: 下载并读取PDF内容...');
            const pdfText = await fetchAndExtractPdfText(pdfUrl);
            if (!pdfText) {
                showError('无法提取PDF文本。请检查PDF链接或文件格式。');
                processButton.disabled = false;
                return;
            }
            console.log("PDF text extracted, length:", pdfText.length);

            showLoading('步骤2/3: 调用Gemini API生成解读...');
            const articleResult = await callGeminiApi(pdfText);
            if (!articleResult) {
                showError('调用Gemini API失败或未返回有效内容。');
                processButton.disabled = false;
                return;
            }
            generatedArticleFullContent = articleResult; // Store the full raw response

            // Parse title from API response
            const lines = articleResult.split('\n');
            let bodyStartIndex = 0;
            if (lines[0] && lines[0].toLowerCase().startsWith('标题：')) {
                generatedArticleTitle = lines[0].substring(3).trim();
                bodyStartIndex = 1;
            } else {
                generatedArticleTitle = "AI论文解读结果"; // Fallback title
            }
            // Join the rest as body (pre will handle formatting)
            const articleBodyForDisplay = lines.slice(bodyStartIndex).join('\n');

            showLoading('步骤3/3: 准备显示结果...');
            outputTitle.textContent = generatedArticleTitle;
            outputContent.textContent = articleBodyForDisplay; // Display content without the "标题：" prefix
            outputSection.style.display = 'block';
            showSuccess('处理完成！');

            // Enable download buttons
            downloadPdfButton.onclick = () => {
                if (originalPdfBlob) {
                    downloadBlob(originalPdfBlob, originalPdfName);
                } else {
                    // Fallback: open the original URL if blob not available (should not happen with current flow)
                    window.open(pdfUrl, '_blank');
                }
            };
            downloadTxtButton.disabled = false;
            downloadPdfButton.disabled = false;

        } catch (error) {
            console.error('处理过程中发生错误:', error);
            showError(`处理失败: ${error.message || '未知错误'}`);
        } finally {
            processButton.disabled = false;
            if (spinnerWrapper) spinnerWrapper.style.display = 'none'; // Ensure spinner is hidden on finish/error
        }
    });

    downloadTxtButton.addEventListener('click', () => {
        if (generatedArticleFullContent) {
            // Use the full content which includes title and tags as per prompt structure
            const txtFileName = `${generatedArticleTitle.replace(/[^a-z0-9\u4e00-\u9fff _-]/gi, '').replace(/\s+/g, '_').substring(0, 50) || 'AI解读'}.txt`;
            downloadText(generatedArticleFullContent, txtFileName);
        }
    });

    async function fetchAndExtractPdfText(pdfUrl) {
        if (typeof pdfjsLib === 'undefined') {
            showError("pdf.js库未能加载，无法处理PDF。");
            return null;
        }
        try {
            const response = await fetch(pdfUrl); // Consider adding CORS proxy if direct fetch fails due to CORS
            if (!response.ok) {
                throw new Error(`下载PDF失败: ${response.status} ${response.statusText}`);
            }
            const pdfData = await response.arrayBuffer();
            originalPdfBlob = new Blob([pdfData], { type: 'application/pdf' }); // Store for download

            const pdf = await pdfjsLib.getDocument({ data: pdfData }).promise;
            let fullText = '';
            for (let i = 1; i <= pdf.numPages; i++) {
                try {
                    const page = await pdf.getPage(i);
                    const textContent = await page.getTextContent();
                    // Attempt to reconstruct paragraphs better
                    let pageText = '';
                    let lastY = -1;
                    textContent.items.forEach(item => {
                        if (lastY !== -1 && item.transform[5] < lastY - (item.height * 0.5) ) { // Heuristic for new line/paragraph
                            pageText += '\n';
                        }
                        pageText += item.str + (item.hasEOL ? '' : ' '); // Add space if not end of line in PDF
                        lastY = item.transform[5];
                    });
                    fullText += pageText.trim().replace(/ +/g, ' ') + '\n\n'; // Add double newline between pages
                } catch (pageError) {
                    console.warn(`处理PDF页面 ${i} 失败:`, pageError);
                    fullText += `[页面 ${i} 内容提取失败]\n\n`;
                }
            }
            return fullText.trim();
        } catch (error) {
            console.error('提取PDF文本失败:', error);
            showError(`提取PDF文本失败: ${error.message}. 检查浏览器控制台获取更多信息.`);
            return null;
        }
    }

    async function callGeminiApi(paperText) {
        if (GEMINI_API_KEY === 'YOUR_GEMINI_API_KEY') {
            showError("请在script.js中配置您的Gemini API密钥!");
            throw new Error("API Key not configured");
        }

        const truncatedPaperText = paperText.substring(0, 30000); // Truncate for API (Gemini has limits)
        // Using the prompt from arxiv.py (professional but engaging, expecting full text)
        const prompt = `作为一位资深的科技内容创作者和分析师，你的任务是根据以下科研论文的文本，撰写一篇既专业准确又不失趣味性的科普解读文章，目标读者是对科技有一定兴趣的普通大众。文章字数在800-900中文字符左右。

请遵循以下指导方针：

1.  **文章标题**：在解读内容的第一行，使用 \`标题：\` 标记。标题应精炼、引人注目，并能准确反映论文的核心贡献或最有趣的发现。例如："AI新突破：机器视觉首次实现X功能"或"深度解析：Y理论如何颠覆我们对Z的认知"。

2.  **开篇**：用简洁的几句话点明研究的背景、试图解决的关键问题及其潜在的重要性或新奇之处，以吸引读者继续阅读。

3.  **核心内容解读**：
    *   **研究动机与背景**：清晰阐述这项研究为何被提出，它针对的是什么现状或挑战。
    *   **方法与技术亮点**：用准确且易于理解的语言解释论文采用的关键方法和技术。如果涉及复杂概念，尝试用简明的方式解释其原理或作用，避免过度简化导致失真。可以保留必要的专业术语，并通过上下文使其易于理解。
    *   **主要发现与成果**：客观、清晰地呈现论文的核心发现和结果。如果论文包含重要数据或性能指标，请准确转述，并解释其意义。
    *   **意义与应用前景**：基于论文的发现，讨论其在学术界或实际应用中可能产生的具体影响、价值和未来发展方向。

4.  **行文风格**：
    *   **语言**：专业、严谨，同时保持文字的生动性和可读性。避免使用过于口语化、情绪化的表达（如过多感叹号、不必要的网络流行语）或不成熟的语气。
    *   **叙述**：逻辑清晰，条理分明，重点突出。确保信息的准确传递。
    *   **平衡性**：在专业深度和大众理解之间取得良好平衡。

5.  **字数控制**：全文（不含标题和标签）控制在800-900中文字符左右。

6.  **结尾标签**：在文章末尾，用 \`标签：\` 标记，另起一行提供3-5个与论文内容高度相关的中文关键词标签，用 # 分隔。例如：#人工智能 #计算机视觉 #科研进展

输出格式约定：
第一行：\`标题：[你创作的标题]\`
第二行开始：文章正文。
最后一行：\`标签：[ #标签1 #标签2 #标签3 ]\`

以下是论文的文本内容：
---\n${truncatedPaperText}\n---\n

请严格按照以上要求，创作出一篇高质量的科普解读文章。`;

        const payload = {
            contents: [{ parts: [{ text: prompt }] }],
            generationConfig: {
                temperature: 0.6, // Adjusted from arxiv.py, can be fine-tuned
                topP: 0.8,
                topK: 40,
                maxOutputTokens: 8192 
            }
        };

        try {
            const response = await fetch(GEMINI_API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: { message: response.statusText } }));
                throw new Error(`Gemini API 错误: ${response.status} ${errorData.error?.message || response.statusText}`);
            }

            const data = await response.json();
            if (data.candidates && data.candidates[0] && data.candidates[0].content && data.candidates[0].content.parts && data.candidates[0].content.parts[0].text) {
                return data.candidates[0].content.parts[0].text;
            }
            throw new Error('API返回了无效的响应结构。');
        } catch (error) {
            console.error('调用Gemini API失败:', error);
            showError(`调用Gemini API失败: ${error.message}`);
            return null;
        }
    }

    function showLoading(message) {
        if (spinnerWrapper) spinnerWrapper.style.display = 'flex'; // Show spinner
        statusMessage.textContent = message;
        statusMessage.className = 'loading';
    }

    function showError(message) {
        if (spinnerWrapper) spinnerWrapper.style.display = 'none'; // Hide spinner
        statusMessage.textContent = message;
        statusMessage.className = 'error';
    }

    function showSuccess(message) {
        if (spinnerWrapper) spinnerWrapper.style.display = 'none'; // Hide spinner
        statusMessage.textContent = message;
        statusMessage.className = 'success';
    }

    function downloadText(text, filename) {
        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    function downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // Function to load and display recommendations
    function loadRecommendations() {
        const recommendationsContainer = document.getElementById('recommendation-cards');
        if (!recommendationsContainer) return;

        // Simulated recommendation data (replace with actual data source later)
        const recommendations = [
            {
                title: "大型语言模型作为优化器",
                authors: "Chengrun Yang, Xuezhi Wang, Yifeng Lu, ...",
                summary: "本文探讨了使用大型语言模型 (LLM) 作为优化器来改进提示和模型参数的可能性。研究表明，LLM 可以通过自然语言指令生成新的优化步骤，从而在各种任务中取得有竞争力的结果。",
                url: "https://arxiv.org/abs/2309.03409",
                pdfUrl: "https://arxiv.org/pdf/2309.03409.pdf"
            },
            {
                title: "通过文本到图像扩散模型生成3D神经辐射场",
                authors: "Jing-Chun Chen, Sida Peng, Dídac Surís, ...",
                summary: "研究者提出了一种新方法，可以利用预训练的文本到图像扩散模型直接从文本提示生成高质量的3D神经辐射场 (NeRF)。这种方法无需3D数据训练，为可控的3D内容生成开辟了新途径。",
                url: "https://arxiv.org/abs/2305.11280",
                pdfUrl: "https://arxiv.org/pdf/2305.11280.pdf"
            },
            {
                title: "视觉语言模型中的涌现能力",
                authors: "Yihan Duan, Rishabh Agarwal, Pranav K S",
                summary: "本文分析了在大型视觉语言模型 (VLM) 中观察到的涌现能力，例如上下文学习和复杂推理。作者讨论了这些能力是如何随着模型规模和数据量的增加而出现的，并探讨了其潜在影响。",
                url: "https://arxiv.org/abs/2306.03409", // Placeholder, update with a real link if available
                pdfUrl: "https://arxiv.org/pdf/2306.03409.pdf" // Placeholder
            }
        ];

        if (recommendations.length === 0) {
            recommendationsContainer.innerHTML = '<p>暂无推荐内容。</p>';
            return;
        }

        recommendationsContainer.innerHTML = ''; // Clear any existing content (like loading message)

        recommendations.forEach(rec => {
            const card = document.createElement('div');
            card.className = 'recommendation-card';

            const titleEl = document.createElement('h3');
            const titleLink = document.createElement('a');
            titleLink.href = rec.url; // Link to the ArXiv abstract page
            titleLink.textContent = rec.title;
            titleLink.target = '_blank'; // Open in new tab
            titleEl.appendChild(titleLink);

            const authorsEl = document.createElement('p');
            authorsEl.className = 'authors';
            authorsEl.textContent = `作者: ${rec.authors}`;

            const summaryEl = document.createElement('p');
            summaryEl.className = 'summary';
            summaryEl.textContent = rec.summary;

            const pdfLinkEl = document.createElement('a');
            pdfLinkEl.href = rec.pdfUrl;
            pdfLinkEl.textContent = '查看/下载PDF';
            pdfLinkEl.className = 'button button-secondary view-pdf-button'; // Added classes for styling
            pdfLinkEl.target = '_blank';

            // Append elements to card
            card.appendChild(titleEl);
            card.appendChild(authorsEl);
            card.appendChild(summaryEl);
            card.appendChild(pdfLinkEl);

            recommendationsContainer.appendChild(card);
        });
    }

    // Call loadRecommendations on DOMContentLoaded
    loadRecommendations();
}); 