## AI 文本检测科研评测工具（非对抗）

本工具用于科研目的，对文本提取一组可复现实验的通用特征，并批量导出为 CSV，方便后续进行统计分析与基线模型构建。工具不包含任何规避/对抗检测功能。

### 目录
- `features.py`：特征提取，包括基本计数、比率、重复度（n-gram）等。
- `baselines.py`：遍历目录内文本，批量导出特征到 CSV。

### 安装依赖
可选：如需更好的中文分词精度，建议安装 `jieba`：

```bash
python -m pip install jieba
```

未安装 `jieba` 时，将回退为基于正则的简单分词（英文词、数字、单字中文）。

### 用法

导出 `generated_articles/` 下所有 `.txt` 的特征到 `ai_detection_eval/output/features.csv`：

```bash
python -m ai_detection_eval.baselines generated_articles ai_detection_eval/output/features.csv
```

输出 CSV 包含以下字段（节选）：
- `num_tokens`：词元数
- `type_token_ratio`：词型-词元比（TTR）
- `hapax_ratio`：只出现一次词的比例
- `average_sentence_length_tokens`：平均句长
- `repeated_trigram_ratio` / `repeated_fourgram_ratio`：重复 3/4-gram 比例
- `english_stopword_ratio` / `chinese_stopword_ratio`：小型停用词比例

你可据此在 notebook 或统计软件中进行：
- 组间差异检验（例如人写 vs 模型写，若有标注）
- 简单分类基线（如逻辑回归、树模型）
- 相关性与回归分析（与质量评分、可读性指标等）

再次强调：本工具仅用于科研评测与分析，不提供也不建议任何针对具体检测器的对抗技巧。


