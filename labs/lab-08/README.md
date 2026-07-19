# AIP444 Lab 8 – Visual Debugger

`img-debug` is a Python command-line tool that analyzes screenshots from terminals, IDEs, browsers, and other developer environments.

The tool can:

- Optimize screenshots before sending them to the model
- Read errors and stack traces from images
- Use Tavily to search current technical documentation
- Provide a structured explanation and recommended fix
- Include source references when web search is used

## Requirements

- Python 3.10 or newer
- OpenRouter API key
- Tavily API key

## Installation

Open a terminal inside the Lab 8 directory:

```bash
cd labs/lab-08
```

Install the required dependencies:

```bash
python -m pip install -r requirements.txt
```

The project uses these Python libraries:

- `openai`
- `python-dotenv`
- `Pillow`
- `tavily-python`
- `pydantic`

## Environment Variables

Add the following API keys to the `.env` file in the repository root:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
TAVILY_API_KEY=your_tavily_api_key
```

An optional model setting can also be added:

```env
OPENROUTER_MODEL=google/gemini-3-flash-preview
```

The `.env` file should not be committed to GitHub.

## Usage

Run the tool by providing the path to an image:

```bash
python img_debug.py screenshot.png
```

A custom instruction can also be included:

```bash
python img_debug.py screenshot.png "Identify the error and provide the smallest safe fix."
```

## Image Optimization

Before sending an image to the model, the tool:

1. Opens the image using Pillow
2. Converts it to RGB
3. Resizes it proportionally if its longest side exceeds 1024 pixels
4. Converts it to JPEG at 85% quality
5. Encodes the JPEG bytes as a Base64 string
6. Prints the original, processed and Base64 sizes to standard error

Example optimization output:

```text
[debug] Original image: 70.42 KB (1298x432)
[debug] Processed JPEG: 64.09 KB (1024x341)
[debug] Base64 string: 85.46 KB (87512 characters)
```

The Base64 string is normally larger than the JPEG because Base64 encoding adds additional characters to represent the binary image data.

## Web Search Tool

The model can call a function named `lookup_error`.

The function sends a focused technical query to the Tavily Search API and returns:

- Search result titles
- Source URLs
- Relevant content
- A Tavily-generated answer when available

The model uses this tool when the error involves:

- A recent framework or package
- Version-specific behaviour
- Unfamiliar error messages
- Documentation that may have changed

## Modern Framework Test

The modern-error test used a screenshot showing a Next.js 16 middleware deprecation message.

Command:

```bash
python img_debug.py modern-error.png "Analyze this Next.js 16 error. You must use lookup_error. Prefer official Next.js documentation and provide the exact complete migration command, including the target directory."
```

The model called the Tavily search tool using this query:

```text
Next.js 16.0.0 migrate middleware.ts to proxy.ts codemod
```

It returned the following migration command:

```bash
npx @next/codemod@latest middleware-to-proxy .
```

The final answer also included references to the official Next.js documentation.

## Terminal Stack-Trace Test

The terminal test used a screenshot containing a multi-level Python traceback.

Command:

```bash
python img_debug.py stack-trace.png "Read the complete stack trace. Identify the exact filename, failing line, call sequence, root cause, and the smallest safe code fix. Use web search only if necessary."
```

The model correctly identified:

- File: `broken_app.py`
- Error: `ZeroDivisionError: division by zero`
- Failing line: line 2
- Failing expression: `return total / count`
- Root cause: `count` was zero because the scores list was empty
- Complete sequence of function calls

The model did not use Tavily because the error was a standard Python issue that did not require current documentation.

## Trick-Image Test

A non-programming image was also tested.

Command:

```bash
python img_debug.py trick-image.jpg "Analyze this image. Only provide debugging instructions if it contains a real programming or technical problem."
```

The model recognized that the image did not contain a programming error and avoided unnecessary debugging instructions and web search.

## Response Structure

The system prompt asks the model to organize its answer using these sections:

```text
## What I See
## Likely Cause
## Recommended Fix
## How to Verify
## References
```

The References section is omitted when Tavily is not used.

## Project Files

```text
lab-08/
├── img_debug.py
├── tools.py
├── SYSTEM_PROMPT.md
├── requirements.txt
├── README.md
├── broken_app.py
├── modern-error.png
├── stack-trace.png
├── test-error.png
└── trick-image.jpg
```

## Running Help

To view the command-line help:

```bash
python img_debug.py --help
```

Example output:

```text
usage: img-debug [-h] image [prompt ...]

Analyze a screenshot using a vision-capable LLM and Tavily web search.
```