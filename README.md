# 🔍 Directory Summarizer [WIP]

> **View `ARCHITECTURE_[date]_[time].md` for a Preview.** 🔼
>
> Pair With 🔗 **[Line Counter](https://github.com/Zfyant/Line_Counter)** to get a fast and detailed summary of your codebase. [Work in Progress]

Directory Summarizer is a powerful Python-only, customizable, open-source tool that scans a project directory, generates a detailed file tree, and provides in-depth analysis of the content of various file types. 

## ✨ Features

- **🌳 File Tree Generation**: Generates a clean and easy-to-read file tree in Markdown format
- **📊 Charts**: Visualize file-type distributions & more
- **🔬 Content Analysis**: Analyzes the content of various file types, including:
    - 🐍 Python (`.py`)
    - 📜 JavaScript/TypeScript (`.js`, `.ts`, `.jsx`, `.tsx`)
    - 🌐 HTML (`.html`, `.htm`)
    - 🎨 CSS (`.css`, `.scss`, `.sass`)
    - 📋 JSON (`.json`)
    - 📝 Markdown (`.md`)
    - ⚡ Batch files (`.bat`, `.cmd`)
    - 🐚 Shell scripts (`.sh`, `.bash`)
- **⚙️ Customizable**: Easily customize the file extensions to analyze, files to skip, and emoji mappings
- **💪 Emoji Support**: Customized emoji mappings to visually distinguish between different file types
- **📊 Brief and Detailed Summaries**: Provides both 1) a brief, one-line summary and 2) a more detailed analysis for each file

## 🚀 Usage

Getting started is super easy! Just run the `Summarizer.py` script from your terminal and provide the path to the directory you want to scan:

```bash
python Summarizer.py

python Summarizer.py --dir "path/to/your/project"
```

🎉 **That's it!** This will generate a Markdown file named `PROJECT_ANALYSIS.md` in the same directory as the script, containing the file tree and content analysis.

## 🔃 Shortcut: Run from anywhere

### One-Click `.bat`
For more flexibility, you can place the `Summarizer.py` script in a central location on your system and run it from any directory using a batch file. An example `.Run_Scanner.bat` is provided.

1.  Place `Summarizer.py` in a dedicated folder, for example `C:\Scripts\`.
    - Make sure the path to `Summarizer.py` inside the `.bat` file is correct.
2.  You can then use the provided `.Run_Scanner.bat` file. Place it in any project folder you want to summarize. The provided bat will use:

    ```batch
    python "C:\Scripts\Summarizer.py" --dir "%CD%"
    ```

Double-click `.Run_Scanner.bat` to generate the summary for the directory it is in.

## 🤝 Contributing

I'd love contributions! 💖 If you have any ideas for new features, improvements, or bug fixes, please:

- 🐛 Open an issue for bug reports
- 💡 Submit a pull request for feature additions
- 🌟 Star the repo if you find it useful!

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for more details. Feel free to use it, modify it, and share it! 🎁
