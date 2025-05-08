# Daily-ArXiv

一个用于自动获取、解读最新ArXiv计算机视觉论文，并生成科普文章及相关图片的Python项目。

## 主要功能

*   **自动获取ArXiv论文**：从ArXiv网站抓取最新的计算机视觉领域论文信息。
*   **PDF处理**：下载论文PDF文件，并从中提取文本内容。
*   **AI驱动的内容生成**：利用Gemini API将专业论文解读为通俗易懂、风格生动的科普文章。
*   **图片提取**：
    *   生成论文首页的截图。
    *   从论文中提取并保存相关的插图。
*   **自动化与手动模式**：提供每日自动处理和手动指定论文处理两种模式。
*   **内容存储**：将生成的科普文章（TXT格式）和提取的图片保存在结构化的目录中。

## 包含的脚本

1.  **`daily.py`**：
    *   **用途**：每日自动运行，从ArXiv的计算机视觉板块（cs.CV/recent）获取指定数量的最新论文。
    *   **处理流程**：自动下载PDF，提取文本，调用Gemini API生成"严谨但生动"风格的科普文章，提取首页截图和插图，并将所有内容按日期和标题保存。
    *   **特点**：无需手动输入，适合每日自动更新内容。

2.  **`arxiv.py`**：
    *   **用途**：手动模式，用户通过命令行输入指定的ArXiv论文PDF链接。
    *   **处理流程**：下载指定PDF，提取完整文本，调用Gemini API生成"严谨但生动"风格（篇幅稍长，约800-900字）的科普文章，并将生成的TXT文件按日期和标题保存。 *（注意：当前`arxiv.py`的图片提取功能可能需要根据`daily.py`的实现进行同步更新）*
    *   **特点**：适合对特定论文进行精细化、深度解读。

## 技术栈与依赖

*   **Python 3.x**
*   **主要Python库**：
    *   `requests`：用于HTTP请求，获取ArXiv页面和下载PDF。
    *   `BeautifulSoup4`：用于解析HTML，从ArXiv页面提取论文信息。
    *   `PyPDF2`：用于基础的PDF文本提取。
    *   `PyMuPDF` (fitz)：用于从PDF中提取内嵌的图片对象。
    *   `pdf2image`：用于将PDF页面转换为图片（生成首页截图）。
*   **外部工具**：
    *   `Poppler`：`pdf2image`的依赖，用于PDF渲染。**必须正确安装并配置到系统PATH。**
*   **API**：
    *   Google Gemini API：用于生成论文解读文章。

## 安装与配置

1.  **克隆项目**（如果您是从版本控制获取）：
    ```bash
    # git clone <repository_url>
    # cd Daily-ArXiv
    ```

2.  **创建并激活Python虚拟环境**（推荐）：
    在项目根目录下执行：
    ```bash
    python3 -m venv .venv  # 创建名为 .venv 的虚拟环境
    source .venv/bin/activate # 激活 (macOS/Linux)
    # .env\Scripts\activate  # 激活 (Windows)
    ```

3.  **安装Python依赖**：
    在激活的虚拟环境中运行：
    ```bash
    pip install requests beautifulsoup4 PyPDF2 PyMuPDF pdf2image
    ```

4.  **安装Poppler**：
    *   **macOS**: `brew install poppler`
    *   **Linux (Debian/Ubuntu)**: `sudo apt-get install poppler-utils`
    *   **Windows**: 
        1.  从可信赖的源（如 [Poppler for Windows on GitHub](https://github.com/oschwartz10612/poppler-windows/releases/)) 下载最新的Poppler二进制文件 (通常是一个.zip或.7z包)。
        2.  解压缩下载的文件到一个稳定的位置（例如 `C:\Program Files\poppler-xxxx`）。
        3.  将解压后Poppler目录下的 `bin` 子目录（例如 `C:\Program Files\poppler-xxxx\bin`）添加到系统的PATH环境变量中。
        4.  重启命令行/终端或IDE以使PATH更改生效。

5.  **配置API密钥**：
    *   打开 `daily.py` 和 `arxiv.py` 文件。
    *   找到 `API_KEY = 'YOUR_GEMINI_API_KEY'` 这一行（或类似）。
    *   将 `'YOUR_GEMINI_API_KEY'` 替换为您自己的有效Google Gemini API密钥。
    *   **安全提示**：直接在代码中硬编码API密钥存在风险。建议使用环境变量等更安全的方式管理密钥，例如：
        ```python
        # API_KEY = os.environ.get('GEMINI_API_KEY')
        ```
        然后在您的环境中设置 `GEMINI_API_KEY` 环境变量。

## 使用方法

确保您的Python虚拟环境已激活。

*   **运行 `daily.py` (自动每日模式)**：
    ```bash
    python daily.py
    ```
    脚本将自动从ArXiv获取最新的 `NUM_PAPERS_TO_PROCESS` (默认为5) 篇cs.CV论文，并进行处理。

*   **运行 `arxiv.py` (手动模式)**：
    ```bash
    python arxiv.py
    ```
    脚本会提示您输入一个ArXiv论文的PDF链接。

## 输出

*   生成的科普文章（`.txt` 文件）和相关图片将保存在项目根目录下的 `generated_articles/` 文件夹中。
*   文本文件名格式：`YYYY-MM-DD_文章标题.txt`。
*   图片将保存在对应文章的子目录中，格式为：`generated_articles/YYYY-MM-DD_文章标题_images/`。
    *   首页截图：`文章标题_first_page.png`
    *   插图：`文章标题_illustration_X.ext` (X为序号，ext为图片原始扩展名)

## 注意事项

*   **ArXiv页面结构**：`daily.py` 的网页抓取逻辑依赖于ArXiv页面的当前HTML结构。如果ArXiv网站更新其结构，可能需要调整`fetch_arxiv_papers`函数中的解析代码。
*   **动态加载**：如果ArXiv的 `recent` 页面严重依赖JavaScript动态加载大量内容，`requests` 可能无法获取所有条目。当前脚本的 `fetch_arxiv_papers` 包含调试日志，若发现获取条目不足，可能需要考虑使用Selenium等浏览器自动化工具代替`requests`。
*   **PDF质量**：PDF文本提取和图片提取的效果很大程度上取决于源PDF的质量和结构。扫描版PDF、加密PDF或包含复杂矢量图形的PDF可能无法完美处理。
*   **API使用**：请注意您使用的Gemini API的调用频率限制和配额。
*   **Poppler依赖**：图片提取（尤其是首页截图）强依赖于Poppler的正确安装和配置。

## 未来可能的改进

*   集成Selenium或Playwright以更稳定地处理动态加载的网页。
*   为图片提取实现更智能的筛选逻辑（例如，基于图片内容、上下文等）。
*   提供配置选项，允许用户通过配置文件或命令行参数修改API密钥、处理论文数量等。
*   增加对已处理论文的记录，避免重复处理。
*   完善错误处理和日志记录机制。