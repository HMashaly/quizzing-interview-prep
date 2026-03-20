# Quizzing Interview Prep
# 🎓 Interview Practice App - Turing College AI Engineering Project

An AI-powered interview preparation application built with Streamlit and OpenAI. Practice for job interviews with an intelligent AI interviewer that adapts to your needs.

## 📋 Project Overview

This application was developed as part of the Turing College AI Engineering Sprint 1 project, demonstrating:
- OpenAI API integration with proper authentication
- Multiple prompt engineering techniques (5+ different approaches)
- Security guards and input validation
- LLM parameter tuning (temperature, top_p, frequency_penalty)
- Real-time cost tracking and token usage monitoring
- Professional UI with Streamlit

## ✨ Features

### Core Interview Features
- 🤖 **AI-powered Interviewer**: Natural conversation with intelligent AI
- 🎯 **Multiple Interview Types**: Technical, Behavioral, or Mixed questions
- 📊 **Difficulty Levels**: Easy, Medium, or Hard questions
- 🧠 **6 Prompt Engineering Techniques**:
  - **Zero-Shot**: Direct questioning without examples
  - **Few-Shot**: Uses examples of good answers as reference
  - **Chain-of-Thought**: Shows reasoning process step-by-step
  - **Role-Play (Strict)**: Demanding interviewer from top tech company
  - **Role-Play (Friendly)**: Supportive, encouraging interviewer
  - **Structured Output**: JSON-formatted feedback with scores

### Advanced Technical Features
- ⚙️ **Tunable LLM Settings**: Temperature, Top P, Frequency Penalty
- 🔒 **Security Guards**: Input validation, jailbreak detection, system prompt validation
- 💰 **Cost Tracking**: Real-time API usage and cost monitoring with budget warnings
- 📝 **Structured JSON Output**: Optional formatted feedback with scores and evaluation
- 🎨 **Professional UI**: Clean, responsive design with Turing College branding

## 🚀 Complete Setup Guide (Step by Step)

### Step 1: Install Python Dependencies

Open your terminal and run:

```bash
# Install all required packages
pip install streamlit openai python-dotenv pandas plotly
# Verify the installation
pip list | grep streamlit
pip list | grep openai
```

### Step 2: Create Your OpenAI API Key File

IMPORTANT: You need an OpenAI API key to use this app. Get one from platform.openai.com/api-keys

Create a file named .env in the same folder as app.py with your API key:

```bash
# Create the .env file
echo "OPENAI_API_KEY=sk-your-actual-api-key-here" > .env

# Verify the file was created
cat .env

```

### Step 3: Run the Application

```bash
# Make sure you're in the folder with app.py
streamlit run app.py
```
