# Property Analysis Auditor

A small Streamlit prototype that independently calculates rental yield and monthly cash flow, compares them with user-entered advertised figures, and explains discrepancies.

## Features
- Rental yield before and after a vacancy allowance
- Monthly cash-flow breakdown
- Checks for differences between calculated and stated yield/cash flow
- Plain-language explanation with a built-in no-key fallback
- Optional Gemini API integration

## Run locally in VS Code

1. Install Python 3.10 or newer and VS Code's Python extension.
2. Open this folder in VS Code.
3. Open Terminal > New Terminal.
4. Create and activate a virtual environment:

### Windows PowerShell
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt and run:
```bat
.venv\Scripts\activate.bat
```

5. Install dependencies:
```bash
python -m pip install -r requirements.txt
```

6. Start the app:
```bash
python -m streamlit run app.py
```

The browser should open at `http://localhost:8501`.

## Optional Gemini API
The application works without an API key. To enable live AI explanations, create a Gemini API key in Google AI Studio and set `GEMINI_API_KEY` as an environment variable before launching Streamlit.

### Windows PowerShell (current terminal only)
```powershell
$env:GEMINI_API_KEY="YOUR_API_KEY_HERE"
python -m streamlit run app.py
```

Do not commit API keys to GitHub. For Streamlit Community Cloud, add `GEMINI_API_KEY` under the app's Settings > Secrets.

## Deploy and share
1. Push `app.py`, `requirements.txt`, `README.md`, and `.gitignore` to a GitHub repository.
2. Sign in at https://share.streamlit.io/ and deploy the repository.
3. Select `app.py` as the main file.
4. If using Gemini, add `GEMINI_API_KEY` in the app's Secrets settings.
5. Share the deployed URL with the hiring manager.

## Important limitations
- This is an independent concept prototype, not an official PropertyLab product and not connected to PropertyLab data.
- Use illustrative inputs unless you have permission to use real data.
- The calculations are simplified and do not include all transaction costs, tax, rate changes, repairs, capital appreciation or financing details.
- A discrepancy means the assumptions may differ; it does not by itself prove a listing is incorrect.
