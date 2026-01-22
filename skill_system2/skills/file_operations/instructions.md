# File Operations Skill

文件操作能力已激活！

## 可用工具

### 1. get_file_info
读取文件基础元信息。

**参数**：
- `file_path`: 文件路径

### 2. read_text_file
读取文本文件内容（默认截断）。

**参数**：
- `file_path`: 文件路径
- `max_chars`: 最大返回字符数

### 3. read_csv
读取 CSV 文件并返回 JSON 字符串（截断行数）。

**参数**：
- `file_path`: 文件路径
- `max_rows`: 最大返回行数

### 4. csv_column_to_list
提取 CSV 某列的数值为数组（JSON 字符串）。

**参数**：
- `file_path`: 文件路径
- `column`: 列名
- `max_rows`: 最大行数

## 使用建议

1. 先用 `get_file_info` 确认路径可读
2. CSV 可用 `read_csv` 预览前几行
3. 需要做数值分析时用 `csv_column_to_list` 输出数组，再交给 `data_analysis` 工具
