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
    const generateLatexButton = document.getElementById('generate-latex-button');
    const spinnerWrapper = document.querySelector('.spinner-wrapper'); // Get the spinner wrapper

    let originalPdfBlob = null;
    let originalPdfName = 'original_paper.pdf';
    let generatedArticleTitle = 'AI解读文章';
    let generatedArticleFullContent = ''; // Store full content with title and tags
    let currentRawPdfText = ''; // To store raw PDF text for LaTeX generation

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
        downloadTxtButton.disabled = true; // Disable buttons during processing
        downloadPdfButton.disabled = true;
        generateLatexButton.disabled = true;

        try {
            showLoading('步骤1/3: 下载并读取PDF内容...');
            const pdfText = await fetchAndExtractPdfText(pdfUrl);
            if (!pdfText) {
                showError('无法提取PDF文本。请检查PDF链接或文件格式。');
                processButton.disabled = false;
                return;
            }
            currentRawPdfText = pdfText; // Store for LaTeX generation
            console.log("PDF text extracted, length:", pdfText.length);

            showLoading('步骤2/3: 调用Gemini API生成解读...');
            const truncatedPaperTextForArticle = currentRawPdfText.substring(0, 30000); // Truncate for API
            const articlePrompt = `作为一位资深的科技内容创作者和分析师，你的任务是根据以下科研论文的文本，撰写一篇既专业准确又不失趣味性的科普解读文章，目标读者是对科技有一定兴趣的普通大众。文章字数在800-900中文字符左右。

请遵循以下指导方针：

1.  **文章标题**：在解读内容的第一行，使用 \`标题：\` 标记。标题应精炼、引人注目，并能准确反映论文的核心贡献或最有趣的发现。例如："AI新突破：机器视觉首次实现X功能"或"深度解析：Y理论如何颠覆我们对Z的认知"。
2.  **开篇**：用简洁的几句话点明研究的背景、试图解决的关键问题及其潜在的重要性或新奇之处，以吸引读者继续阅读。
3.  **核心内容解读**：
    *   研究动机与背景
    *   方法与技术亮点
    *   主要发现与成果
    *   意义与应用前景
4.  **行文风格**：专业、严谨，同时生动可读。
5.  **字数控制**：全文（不含标题和标签）控制在800-900中文字符左右。
6.  **结尾标签**：在文章末尾，用 \`标签：\` 标记，另起一行提供3-5个与论文内容高度相关的中文关键词标签，用 # 分隔。

输出格式约定：
第一行：\`标题：[你创作的标题]\`
第二行开始：文章正文。
最后一行：\`标签：[ #标签1 #标签2 #标签3 ]\`

以下是论文的文本内容：
---
${truncatedPaperTextForArticle}
---

请严格按照以上要求，创作出一篇高质量的科普解读文章。`;

            const articleResult = await callGeminiApi(articlePrompt); // Pass constructed prompt
            if (!articleResult) {
                showError('调用Gemini API失败或未返回有效内容。');
                processButton.disabled = false;
                return;
            }
            generatedArticleFullContent = articleResult;

            const lines = articleResult.split('\n');
            let bodyStartIndex = 0;
            let titleLine = '';
            if (lines[0] && lines[0].toLowerCase().startsWith('标题：')) {
                titleLine = lines[0];
                generatedArticleTitle = titleLine.substring(3).trim();
                bodyStartIndex = 1; // المقبل
            } else {
                generatedArticleTitle = "AI论文解读结果";
            }

            let articleBodyForDisplay;
            if (bodyStartIndex > 0) {
                // If there was a title line, get content after it
                articleBodyForDisplay = articleResult.substring(titleLine.length).trim();
            } else {
                // If no title line detected, use the whole result as body
                articleBodyForDisplay = articleResult.trim();
            }

            // Normalize newlines: replace any CR LF (Windows) or CR (old Mac) with LF
            articleBodyForDisplay = articleBodyForDisplay.replace(/\r\n|\r/g, '\n');

            // Ensure distinct paragraphs: Replace 3+ newlines with 2, and 2 newlines remain 2.
            // This helps <pre> show a blank line between paragraphs if the source had them.
            articleBodyForDisplay = articleBodyForDisplay.replace(/\n{3,}/g, '\n\n');

            // Attempt to add paragraph breaks around **headings** if they aren't already well-separated.
            // This looks for non-whitespace, optional space, then **heading**, ensuring a newline before.
            articleBodyForDisplay = articleBodyForDisplay.replace(/([^\n])\s*(\*\*[^\*]+\*\*)/g, '$1\n\n$2');
            // This looks for **heading**, optional space, then non-whitespace, ensuring newlines after.
            articleBodyForDisplay = articleBodyForDisplay.replace(/(\*\*[^\*]+\*\*)\s*([^\n])/g, '$1\n\n$2');
            
            // Trim leading/trailing newlines that might have been added excessively
            articleBodyForDisplay = articleBodyForDisplay.trim();

            showLoading('步骤3/3: 准备显示结果...');
            outputTitle.textContent = generatedArticleTitle;
            outputContent.textContent = articleBodyForDisplay;
            outputSection.style.display = 'block';
            showSuccess('处理完成！');

            downloadPdfButton.onclick = () => {
                if (originalPdfBlob) {
                    downloadBlob(originalPdfBlob, originalPdfName);
                } else {
                    window.open(pdfUrl, '_blank');
                }
            };
            downloadTxtButton.disabled = false;
            downloadPdfButton.disabled = false;
            generateLatexButton.disabled = false; // Enable LaTeX button

        } catch (error) {
            console.error('处理过程中发生错误:', error);
            showError(`处理失败: ${error.message || '未知错误'}`);
        } finally {
            processButton.disabled = false;
            if (spinnerWrapper) spinnerWrapper.style.display = 'none';
        }
    });

    downloadTxtButton.addEventListener('click', () => {
        if (generatedArticleFullContent) {
            const txtFileName = `${generatedArticleTitle.replace(/[^a-z0-9\\u4e00-\\u9fff _-]/gi, '').replace(/\\s+/g, '_').substring(0, 50) || 'AI解读'}.txt`;
            downloadText(generatedArticleFullContent, txtFileName);
        }
    });

    generateLatexButton.addEventListener('click', async () => {
        if (!currentRawPdfText || !generatedArticleTitle) {
            showError("请先成功解读一篇论文，再生成演示文稿。");
            return;
        }
        await handleGenerateLatexClick(currentRawPdfText, generatedArticleTitle);
    });

    async function handleGenerateLatexClick(rawPdfText, articleTitle) {
        showLoading('正在生成LaTeX演示文稿 (这可能需要一些时间)...');
        generateLatexButton.disabled = true;

        try {
            const truncatedPaperTextForLatex = rawPdfText.substring(0, 28000);

            const escapeLatex = (text) => {
                if (typeof text !== 'string') return '';
                return text.replace(/[&%$#_{}\\\\\\[\\]~^]/g, (match) => {
                    const replacements = {
                        '&': '\\\\&',
                        '%': '\\\\%',
                        '$': '\\\\$',
                        '#': '\\\\#',
                        '_': '\\\\_',
                        '{': '\\\\{',
                        '}': '\\\\}',
                        '~': '\\\\textasciitilde{}',
                        '^': '\\\\textasciicircum{}',
                        '\\\\': '\\\\textbackslash{}',
                        '[': '{[}', // Less common, but can be problematic
                        ']': '{]}'
                    };
                    return replacements[match] || match;
                });
            };

            const safeArticleTitle = escapeLatex(articleTitle);
            const shortSafeArticleTitle = escapeLatex(articleTitle.substring(0,40));

            const latexPrompt = `You are an expert LaTeX Beamer presentation creator. Your mission is to generate a complete LaTeX Beamer source file (.tex) based on the research paper text provided below. All textual content in the presentation (titles, section names, bullet points, summaries, etc.) MUST be in ENGLISH.\n\nStrictly adhere to the following LaTeX Beamer template structure. Replace placeholders like '[FULL_ENGLISH_PAPER_TITLE]', '[ENGLISH_PAPER_AUTHORS]', section content comments, etc., with relevant information extracted FROM THE PROVIDED PAPER TEXT, ensuring all such generated content is in ENGLISH.\n\nLaTeX Beamer Template to use (fill in the content in ENGLISH):\n\`\`\`latex\n\\documentclass{beamer}\n\n\\mode<presentation> {\n\\usetheme{CambridgeUS}\n\\usecolortheme{wolverine}\n% \\setbeamertemplate{navigation symbols}{}\n}\n\n\\usepackage{graphicx}\n\\usepackage{booktabs}\n\\usepackage[UTF8,noindent]{ctexcap} % Retained as per original template, ensure English output is compatible.\n\\usepackage[bookmarks=true]{hyperref}\n\n% --- TITLE PAGE --- \n\\title[${shortSafeArticleTitle}]{${safeArticleTitle}}\n\\author{[Paper Authors - Extracted, IN ENGLISH]}\n\\institute[[Institute Abbreviation - Extracted, IN ENGLISH]]{\n  [Full Institute Name - Extracted, IN ENGLISH] \\\\\n  \\medskip\n  % \\textit{[Optional: Author Email]}\n}\n\\date{\\today}\n\n\\begin{document}\n\n\\begin{frame}\n  \\titlepage\n\\end{frame}\n\n\\begin{frame}\n  \\frametitle{Overview}\n  \\tableofcontents\n\\end{frame}\n\n% --- PRESENTATION SLIDES (ALL CONTENT MUST BE GENERATED IN ENGLISH) --- \n\n\\section{Introduction}\n  \\begin{frame}\n    \\frametitle{Introduction: Background and Contributions}\n    % - Extract key background points from the paper (in English).\n    % - Summarize main contributions (in English).\n    % - Use itemize for bullet points.\n    \\begin{itemize}\n      \\item Placeholder: Point 1 about background or contribution (in English).\n      \\item Placeholder: Point 2 about background or contribution (in English).\n    \\end{itemize}\n  \\end{frame}\n\n\\subsection{Problem Statement} % Example: adapt as needed\n  \\begin{frame}\n    \\frametitle{Problem Statement}\n    % - Clearly state the problem the paper addresses (in English).\n  \\end{frame}\n\n\\section{Related Work} % If significant and present in the paper\n  \\begin{frame}\n    \\frametitle{Related Work}\n    % - Summarize key related works discussed in the paper (in English).\n  \\end{frame}\n\n\\section{Methodology}\n  \\begin{frame}\n    \\frametitle{Proposed Method / Framework}\n    % - Describe the core methodology of the paper (in English).\n    % - Use blocks or columns if helpful for clarity.\n  \\end{frame}\n  \\subsection{Key Components} % Example: adapt as needed\n  \\begin{frame}\n    \\frametitle{Key Components / Algorithm}\n    % - Detail specific parts of the method or algorithm (in English).\n    % \\begin{block}{Component 1 (English)}\n    %   Details...\n    % \\end{block}\n  \\end{frame}\n\n\\section{Experiments and Results}\n  \\begin{frame}\n    \\frametitle{Experimental Setup}\n    % - Describe datasets, metrics, and setup (in English).\n  \\end{frame}\n  \\begin{frame}\n    \\frametitle{Results and Discussion}\n    % - Present key findings and results (in English).\n    % - Use itemize or tables if appropriate.\n    % E.g.,\n    % \\begin{table}\n    %   \\centering\n    %   \\begin{tabular}{ll}\n    %     \\toprule\n    %     Metric & Value \\\\\n    %     \\midrule\n    %     Accuracy & 90% \\\\\n    %     \\bottomrule\n    %   \\end{tabular}\n    %   \\caption{Key experimental results (English).}\n    % \\end{table}\n  \\end{frame}\n\n\\section{Conclusion}\n  \\begin{frame}\n    \\frametitle{Conclusion and Future Work}\n    % - Summarize the paper\'s conclusions (in English).\n    % - Mention any future work suggested (in English).\n  \\end{frame}\n\n% \\section{References} % Optional, if key references are highlighted in slides\n%   \\begin{frame}\n%     \\frametitle{Key References}\n%     \\footnotesize{\n%       \\begin{thebibliography}{99}\n%         % \\bibitem[Smith, 2023]{ref1} Smith, J. et al. (2023). Title of relevant paper. \\emph{Journal}.\n%       \\end{thebibliography}\n%     }\n%   \\end{frame}\n\n\\begin{frame}\n  \\Huge{\\centerline{Thank You}}\n\\end{frame}\n\n\\end{document}\n\`\`\`\n\nPaper text to process:\n---\n${truncatedPaperTextForLatex}\n---\n\nImportant Output Instructions:\n1.  ONLY output the complete LaTeX Beamer source code, starting with \\documentclass{beamer} and ending with \\end{document}.\n2.  Ensure all textual content derived from the paper is in ENGLISH.\n3.  Do NOT include any Markdown formatting (like \`\`\`latex or \`\`\`) around the LaTeX code output.\n4.  Faithfully use the provided Beamer theme and packages.\n5.  Properly escape any special LaTeX characters within the content extracted from the paper (e.g., %, $, _, #, &, {, }).\n`;

            let latexCode = await callGeminiApi(latexPrompt);

            if (latexCode) {
                latexCode = latexCode.replace(/^```latex\\s*|^```tex\\s*|^```\\s*/im, '');
                latexCode = latexCode.replace(/\\s*```$/im, '');
                latexCode = latexCode.trim();

                if (!latexCode.startsWith('\\\\documentclass{beamer}')) {
                    console.warn("Output from API does not start with \\documentclass. Attempting to find correct start.");
                    const documentclassIndex = latexCode.indexOf('\\\\documentclass{beamer}');
                    if (documentclassIndex !== -1) {
                        latexCode = latexCode.substring(documentclassIndex);
                    }
                }

                const texFileName = `${articleTitle.replace(/[^a-z0-9\\u4e00-\\u9fff _-]/gi, '').replace(/\\s+/g, '_').substring(0, 50) || 'presentation'}.tex`;
                downloadLatex(latexCode, texFileName);
                showSuccess('LaTeX演示文稿已生成并开始下载！');
            } else {
                showError('生成LaTeX演示文稿失败，未收到有效内容。');
            }

        } catch (error) {
            console.error('生成LaTeX演示文稿过程中发生错误:', error);
            showError(`生成LaTeX失败: ${error.message || '未知错误'}`);
        } finally {
            generateLatexButton.disabled = false;
            if (spinnerWrapper) spinnerWrapper.style.display = 'none';
        }
    }
    
    function downloadLatex(text, filename) {
        const blob = new Blob([text], { type: 'application/x-latex;charset=utf-8' }); // Or 'text/plain'
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

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

    // Modified to accept full prompt text
    async function callGeminiApi(fullPromptText) { 
        if (GEMINI_API_KEY === 'YOUR_GEMINI_API_KEY') {
            showError("请在script.js中配置您的Gemini API密钥!");
            throw new Error("API Key not configured");
        }

        // The fullPromptText now includes the paper text, so no need to append truncatedPaperText here.
        // The truncation should happen *before* constructing the fullPromptText if needed.

        const payload = {
            contents: [{ parts: [{ text: fullPromptText }] }], // Use the passed fullPromptText
            generationConfig: {
                temperature: 0.6,
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
            const fullSummary = rec.summary;
            const shortSummaryLength = 150; // Characters to show initially
            if (fullSummary.length > shortSummaryLength) {
                summaryEl.textContent = fullSummary.substring(0, shortSummaryLength) + "...";
                const readMoreLink = document.createElement('a');
                readMoreLink.href = '#';
                readMoreLink.className = 'read-more-link';
                readMoreLink.textContent = '阅读更多';
                readMoreLink.onclick = (e) => {
                    e.preventDefault();
                    if (readMoreLink.textContent === '阅读更多') {
                        summaryEl.textContent = fullSummary;
                        readMoreLink.textContent = '收起';
                    } else {
                        summaryEl.textContent = fullSummary.substring(0, shortSummaryLength) + "...";
                        readMoreLink.textContent = '阅读更多';
                    }
                };
                summaryEl.appendChild(document.createElement('br')); // Add a line break before the link
                summaryEl.appendChild(readMoreLink);
            } else {
                summaryEl.textContent = fullSummary;
            }

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