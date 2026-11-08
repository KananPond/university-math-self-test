# 大学数学自测

本仓库收录两套可离线运行的大学数学考试模拟系统：

- [复变函数](./复变函数/README.md)：复数运算、复平面可视化、闪电训练与在线判分。
- [线性代数](./线性代数/README.md)：矩阵可视化、精确分数判分与在线考试。

两套系统都使用 Python 标准库和原生 JavaScript 实现，不需要安装第三方
Python 或 Node.js 依赖，也不需要联网。题库、答案和判分逻辑分别保存在对应
科目的目录中。

## 环境要求

- Python 3.8 或更高版本
- Windows、Linux 或 macOS
- 使用浏览器访问本机服务

## 快速开始

### Windows

进入对应科目的 `web_exam` 目录，双击启动脚本：

```text
复变函数\web_exam\start.bat
线性代数\web_exam\start.bat
```

也可以在 PowerShell 中指定端口启动：

```powershell
python .\复变函数\web_exam\server.py 8767
python .\线性代数\web_exam\server.py 8766
```

启动后访问：

- 复变函数：<http://127.0.0.1:8767/>
- 线性代数：<http://127.0.0.1:8766/>

### Linux / macOS / WSL

```bash
cd 复变函数/web_exam
./start.sh

cd ../../线性代数/web_exam
./start.sh
```

启动脚本会检查 Python、启动本地 HTTP 服务并尝试打开浏览器。服务只监听
`127.0.0.1`，不会对外网开放。按 `Ctrl+C` 可停止服务。

## 题库维护与验证

题库格式约定在各科目的 `bank/FORMAT.md` 中。修改题库后，在对应科目目录
运行生成和校验脚本：

```powershell
python .\build_paper.py
python .\verify_paper.py
```

在线系统的测试位于各自的 `web_exam/tests/` 目录。复变函数测试可直接运行：

```powershell
python -m unittest discover -s .\复变函数\web_exam\tests
```

线性代数包含 Python 测试和 Node.js 端到端测试；端到端测试需要先在一个
终端启动 `线性代数\web_exam\server.py`，再运行测试脚本。

## 目录结构

```text
.
├── 复变函数/
│   ├── bank/                 复变函数题库与精确复数运算
│   ├── web_exam/             在线考试服务与前端
│   ├── build_paper.py        生成样卷、答案和题库总览
│   └── verify_paper.py       题库与答案校验
└── 线性代数/
    ├── bank/                 线性代数题库与精确分数运算
    ├── web_exam/             在线考试服务与前端
    ├── build_paper.py        生成样卷、答案和题库总览
    └── verify_paper.py       题库与答案校验
```

考试记录会写入对应的 `web_exam/records/` 目录；这些本地生成文件不会纳入
版本控制。

## 使用说明

本项目用于个人学习、自测和练习，不具备监考功能。题库中的答案和解析由
服务端保存，浏览器端只接收当前试卷所需的公开题面。