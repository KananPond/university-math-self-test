# University Math Self-Test

An offline university mathematics exam simulator and self-study toolkit for
complex analysis and linear algebra.

This repository contains two independent, browser-based exam systems:

- [Complex Analysis](./复变函数/README.md): complex-number operations, complex-plane
  visualization, lightning drills, and online grading.
- [Linear Algebra](./线性代数/README.md): matrix visualization, exact-fraction
  grading, and online examinations.

Both systems use only the Python standard library and vanilla JavaScript.
They require no third-party Python or Node.js packages and work fully offline.
Question banks, answer keys, and grading logic are kept in each subject's
directory.

## Requirements

- Python 3.8 or later
- Windows, Linux, or macOS
- A modern web browser

## Quick start

### Windows

Open the corresponding `web_exam` directory and double-click its launcher:

```text
复变函数\web_exam\start.bat
线性代数\web_exam\start.bat
```

Or start a server from PowerShell with a custom port:

```powershell
python .\复变函数\web_exam\server.py 8767
python .\线性代数\web_exam\server.py 8766
```

Then open:

- Complex Analysis: <http://127.0.0.1:8767/>
- Linear Algebra: <http://127.0.0.1:8766/>

### Linux / macOS / WSL

```bash
cd 复变函数/web_exam
./start.sh

cd ../../线性代数/web_exam
./start.sh
```

The launchers check for Python, start a local HTTP server, and try to open the
browser. The services listen only on `127.0.0.1`. Press `Ctrl+C` to stop them.

## Maintaining and validating question banks

Question formats are documented in each subject's `bank/FORMAT.md`. After
editing a question bank, run these commands from that subject's directory:

```powershell
python .\build_paper.py
python .\verify_paper.py
```

Tests are located under each `web_exam/tests/` directory. The generated exam
records are stored in `web_exam/records/` and are excluded from version control.

## Directory structure

```text
.
├── 复变函数/
│   ├── bank/                 Complex-analysis question bank and exact arithmetic
│   ├── web_exam/             Online exam service and frontend
│   ├── build_paper.py        Generate sample papers, answers, and an overview
│   └── verify_paper.py       Validate the question bank and answers
└── 线性代数/
    ├── bank/                 Linear-algebra question bank and exact fractions
    ├── web_exam/             Online exam service and frontend
    ├── build_paper.py        Generate sample papers, answers, and an overview
    └── verify_paper.py       Validate the question bank and answers
```

Exam records are written to the corresponding `web_exam/records/` directory.
These locally generated files are not tracked by version control.

## Usage notes

This project is intended for personal study, self-testing, and practice. It
does not provide proctoring. Answers and explanations remain on the server;
the browser receives only the public question data needed for the current exam.

## License

This project is released under the [MIT License](./LICENSE).

