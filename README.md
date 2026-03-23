# Quizzing Interview Prep
# 🎓 Interview Practice App - Turing College AI Engineering Project

An AI-powered interview preparation application built with Streamlit and OpenAI. Practice for job interviews with an intelligent AI interviewer that adapts to your needs.

**Live app:** [Streamlit Cloud deployment](https://quizzing-interview-prep.streamlit.app)

## 📋 Project Overview

This application was developed as part of the Turing College AI Engineering Sprint 1 project, demonstrating:
- OpenAI API integration (API key entered only in the **sidebar** password field — not read from `.env` or environment variables)
- **Five** distinct prompt-engineering techniques (see list below — matches `PROMPT_TECHNIQUES` in `app.py`)
- Security guards: input validation, jailbreak-style phrase checks, and system-prompt template checks
- LLM parameter tuning (temperature, top_p, frequency_penalty)
- Approximate cumulative cost and token totals (rough per-model rates for display only)
- Optional structured JSON replies when the sidebar checkbox is enabled
- Professional UI with Streamlit

## ✨ Features

### Core Interview Features
- 🤖 **AI-powered Interviewer**: Natural conversation with intelligent AI
- 🎯 **Multiple Interview Types**: Technical, Behavioral, or Mixed questions
- 📊 **Difficulty Levels**: Easy, Medium, or Hard questions
- 🧠 **Five prompt engineering techniques** (same names as in the app):
  - **Zero-shot**: Direct questioning without examples
  - **Few-shot**: Examples of strong answers to set expectations
  - **Chain-of-Thought**: Step-by-step reasoning and follow-ups
  - **Self-Consistency**: Candidate reflects on and improves their own answers
  - **Role-based**: Questions framed for a target role’s responsibilities
- 📝 **Optional structured JSON**: Sidebar option — assistant replies as JSON (`message` + `evaluation`) when enabled

### Advanced Technical Features
- ⚙️ **Tunable LLM settings**: Model (GPT-4.1 / 4.1 mini / 4.1 nano / 4o / 4o mini), temperature, top_p, frequency penalty
- 🔒 **Security guards**: Chat and optional topic/job fields validated; system templates checked before interview start
- 💰 **Cost display**: Running **approximate** USD cost and token count in the sidebar (not official billing; no budget cap or alerts)
- 🎨 **Professional UI**: Turing College branding in the sidebar

## 🚀 Complete Setup Guide (Step by Step)

### Step 1: Install Python Dependencies

Open your terminal and run:

```bash
# Install all required packages
pip install -r requirements.txt
# Verify the installation
pip list | grep streamlit
pip list | grep openai
```

### Deploy on Streamlit Community Cloud

If install fails on the cloud with **Pillow / zlib** or **pandas** build errors, the environment is usually **Python 3.13+** (e.g. 3.14) while old pinned packages have **no pre-built wheels** and try to compile from source.

1. In [share.streamlit.io](https://share.streamlit.io/), open your app → **Manage app** → **Settings**.
2. Under **Advanced settings**, set **Python version** to **3.12** (recommended). Redeploy if you change it.
3. This repo’s `requirements.txt` lists `streamlit` and `openai`.

The **SetuptoolsDeprecationWarning** about license classifiers is a harmless upstream warning during dependency installs.

### Step 2: OpenAI API key

Get a key from [platform.openai.com/api-keys](https://platform.openai.com/api-keys).

**The app only uses the sidebar text field** (masked as a password). It does **not** read `OPENAI_API_KEY` from the environment, `.env`, or Streamlit Secrets. Each user pastes their own key when they open the app.

Do not commit API keys to the repository.

### Step 3: Run the Application

```bash
# Make sure you're in the folder with app.py
streamlit run app.py
```
