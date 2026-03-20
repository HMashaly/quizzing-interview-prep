import streamlit as st
import openai
from dotenv import load_dotenv
import os
import json
import hashlib
from datetime import datetime

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Interview Practice - Turing College", page_icon="🎓")

# ===== SECURITY GUARD: Input validation and sanitization =====
def validate_input(text):
    """Security guard: Validate and sanitize user input"""
    if not text or len(text.strip()) == 0:
        return False, "Input cannot be empty"
    if len(text) > 5000:
        return False, "Input too long (max 5000 characters)"
    
    # Block common jailbreak attempts
    blocked_patterns = [
        "ignore previous instructions",
        "forget your role",
        "you are now",
        "system prompt",
        "jailbreak"
    ]
    
    text_lower = text.lower()
    for pattern in blocked_patterns:
        if pattern in text_lower:
            return False, f"Input contains blocked content: '{pattern}'"
    
    return True, text[:5000]  # Truncate if needed

# ===== PROMPT ENGINEERING TECHNIQUES (5 different system prompts) =====
PROMPT_TECHNIQUES = {
    "Zero-Shot": {
        "description": "Direct questioning without examples",
        "system_prompt": "You are a professional interviewer. Ask interview questions directly."
    },
    "Few-Shot": {
        "description": "Provides examples of good answers",
        "system_prompt": """You are a professional interviewer. Here are examples of good interview responses:
        
Example 1: "I led a team of 5 developers to deliver a project 2 weeks ahead of schedule by implementing agile methodologies."
Example 2: "When faced with a critical bug, I systematically debugged by isolating components and using unit tests."

Use these as reference for evaluating answers."""
    },
    "Chain-of-Thought": {
        "description": "Shows reasoning process in responses",
        "system_prompt": """You are a professional interviewer who thinks step-by-step.
        
When evaluating answers:
1. First, identify the key points in the candidate's response
2. Then, assess technical accuracy
3. Next, evaluate communication clarity
4. Finally, provide structured feedback
Show your reasoning process in your responses."""
    },
    "Role-Play (Strict)": {
        "description": "Acts as a strict, demanding interviewer",
        "system_prompt": """You are a strict, demanding interviewer from a top tech company.
        
Rules:
- Ask challenging, technical questions
- Push back on vague answers
- Require specific examples and details
- Keep responses professional but firm
- Don't give compliments easily"""
    },
    "Role-Play (Friendly)": {
        "description": "Acts as a supportive, encouraging interviewer",
        "system_prompt": """You are a friendly, supportive interviewer who helps candidates succeed.
        
Rules:
- Start with positive reinforcement
- Provide constructive feedback gently
- Encourage elaboration with kind prompts
- Celebrate good answers enthusiastically
- Create a comfortable interview environment"""
    },
    "Structured Output": {
        "description": "Provides feedback in JSON format",
        "system_prompt": """You are a professional interviewer. Provide feedback in JSON format with:
- score: number from 1-10
- strengths: array of strengths
- improvements: array of areas to improve
- next_question: the next interview question
- evaluation: detailed evaluation text"""
    }
}

# Custom CSS for better UI
st.markdown("""
<style>
    /* Turing College branding colors */
    :root {
        --tc-primary: #0066CC;
        --tc-secondary: #00A3FF;
        --tc-accent: #FF6B00;
    }
    
    .main > div {
        padding-bottom: 100px;
        height: 100vh;
        display: flex;
        flex-direction: column;
    }
    
    .stChatMessageContainer {
        flex-grow: 1;
        overflow-y: auto;
        margin-bottom: 20px;
    }
    
    .stChatInput {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 20px;
        z-index: 100;
        border-top: 1px solid #eee;
    }
    
    @media (min-width: 768px) {
        .stChatInput {
            left: 21rem;
        }
    }
    
    /* Turing College branding */
    .tc-header {
        background: linear-gradient(135deg, var(--tc-primary), var(--tc-secondary));
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    
    .security-badge {
        background-color: #f0f9ff;
        border-left: 4px solid var(--tc-accent);
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'interview_started' not in st.session_state:
    st.session_state.interview_started = False
if 'job_context' not in st.session_state:
    st.session_state.job_context = "Python Developer"
if 'difficulty' not in st.session_state:
    st.session_state.difficulty = "Medium"
if 'interview_type' not in st.session_state:
    st.session_state.interview_type = "Mixed"
if 'prompt_technique' not in st.session_state:
    st.session_state.prompt_technique = "Zero-Shot"
if 'structured_output' not in st.session_state:
    st.session_state.structured_output = False
if 'total_tokens' not in st.session_state:
    st.session_state.total_tokens = 0
if 'total_cost' not in st.session_state:
    st.session_state.total_cost = 0.0

# ===== COST CALCULATION FUNCTION =====
def calculate_cost(model_name, input_tokens, output_tokens):
    """Calculate API call cost"""
    pricing = {
        "GPT-4o mini": {"input": 0.00015, "output": 0.0006},  # per 1K tokens
        "GPT-4o": {"input": 0.0025, "output": 0.01},
        "GPT-3.5 Turbo": {"input": 0.0005, "output": 0.0015}
    }
    
    model_key = next((m for m in pricing.keys() if m in model_name), "GPT-4o mini")
    prices = pricing[model_key]
    
    input_cost = (input_tokens / 1000) * prices["input"]
    output_cost = (output_tokens / 1000) * prices["output"]
    
    return input_cost + output_cost

# ===== SECURITY GUARD: System prompt validation =====
def validate_system_prompt(prompt):
    """Security guard: Ensure system prompt doesn't contain harmful instructions"""
    harmful_patterns = [
        "ignore safety",
        "bypass restrictions",
        "harmful",
        "illegal",
        "unethical"
    ]
    
    prompt_lower = prompt.lower()
    for pattern in harmful_patterns:
        if pattern in prompt_lower:
            return False, f"System prompt contains blocked content: '{pattern}'"
    
    return True, prompt

# SIDEBAR
with st.sidebar:
    # Turing College branding
    st.markdown("""
    <div class="tc-header">
        <h2>🎓 Turing College</h2>
        <p>AI Engineering - Interview Practice</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.title("🎯 Interview Settings")
    
    # ===== PROMPT TECHNIQUE SELECTION (Requirement: 5 different techniques) =====
    st.markdown("### 🧠 Prompt Engineering Technique")
    selected_technique = st.selectbox(
        "Choose prompting technique:",
        list(PROMPT_TECHNIQUES.keys()),
        key="prompt_technique_select"
    )
    
    if selected_technique != st.session_state.prompt_technique:
        st.session_state.prompt_technique = selected_technique
        if st.session_state.interview_started:
            st.session_state.messages = []  # Reset chat when technique changes
    
    st.info(f"**{selected_technique}:** {PROMPT_TECHNIQUES[selected_technique]['description']}")
    
    # Structured output option
    st.markdown("### 📊 Output Format")
    structured_output = st.checkbox("Use structured JSON output", key="structured_output_check")
    st.session_state.structured_output = structured_output
    
    st.markdown("### What to practise")
    interview_type = st.selectbox(
        "Interview type:",
        ["Technical", "Behavioral", "Mixed"],
        key="interview_type_select"
    )
    
    st.markdown("### Difficulty")
    difficulty = st.select_slider(
        "Difficulty level:",
        options=["Easy", "Medium", "Hard"],
        value="Medium",
        key="difficulty_select"
    )
    
    st.markdown("### Topic (optional)")
    topic = st.text_input("", placeholder="e.g., Python, System Design, Leadership")
    
    st.markdown("### Job description (optional)")
    job_desc_input = st.text_area("", placeholder="Paste job description here...", height=100)

    # ===== LLM SETTINGS (Multiple settings for tuning) =====
    st.markdown("---")
    st.markdown("### ⚙️ LLM Settings")
    
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1, 
                           help="Lower = more focused, higher = more creative")
    
    top_p = st.slider("Top P", 0.0, 1.0, 1.0, 0.05,
                     help="Nucleus sampling - lower = more focused")
    
    frequency_penalty = st.slider("Frequency Penalty", -2.0, 2.0, 0.0, 0.1,
                                  help="Reduce repetition of tokens")
    
    st.markdown("### 🤖 AI Model")
    model = st.selectbox(
        "",
        ["GPT-4o mini", "GPT-4o", "GPT-3.5 Turbo"],
        key="model_select"
    )
    
    # ===== SECURITY GUARD: Input validation indicator =====
    st.markdown("---")
    st.markdown("### 🔒 Security")
    st.markdown("""
    <div class="security-badge">
        ✅ Input validation active<br>
        ✅ Jailbreak detection<br>
        ✅ System prompt validation
    </div>
    """, unsafe_allow_html=True)
    
    # Cost tracking display
    if st.session_state.total_cost > 0:
        st.metric("💰 Total API Cost", f"${st.session_state.total_cost:.4f}")
        st.metric("🔢 Total Tokens", st.session_state.total_tokens)
    
    # Start interview button
    if st.button("🚀 Start interview", type="primary", use_container_width=True):
        st.session_state.interview_started = True
        st.session_state.messages = []
        st.rerun()

# Main chat area
st.title("💬 Interview Practice with AI")

# Turing College course info
st.caption("🎓 Turing College | AI Engineering | Sprint 1 Project")

# Show settings summary when interview not started
if not st.session_state.interview_started:
    st.markdown("Configure your interview settings in the sidebar and click **Start interview** to begin.")
    
    # Show preview of settings
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Type", st.session_state.interview_type)
    with col2:
        st.metric("Difficulty", st.session_state.difficulty)
    with col3:
        st.metric("Model", model)
    with col4:
        st.metric("Technique", selected_technique)

# Interview in progress
if st.session_state.interview_started:
    # Create a container for chat messages
    chat_container = st.container()
    
    with chat_container:
        # Display all messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                # Handle structured output display
                if message["role"] == "assistant" and st.session_state.structured_output:
                    try:
                        data = json.loads(message["content"])
                        st.json(data)
                    except:
                        st.markdown(message["content"])
                else:
                    st.markdown(message["content"])
        
        # If no messages yet, show welcome and first question
        if len(st.session_state.messages) == 0:
            with st.chat_message("assistant"):
                welcome_msg = f"""👋 Hello! I'm your AI interviewer.

I'm using **{selected_technique}** prompting technique.
I'll be asking you **{difficulty}** questions for a **{interview_type}** interview.

Let's begin with your first question:"""
                st.markdown(welcome_msg)
                
                # Get system prompt from selected technique
                technique = PROMPT_TECHNIQUES[selected_technique]
                system_prompt = technique["system_prompt"]
                
                # ===== SECURITY GUARD: Validate system prompt =====
                is_valid, validated_prompt = validate_system_prompt(system_prompt)
                if not is_valid:
                    st.error(f"Security validation failed: {validated_prompt}")
                    st.stop()
                
                # Generate first question
                with st.spinner("Preparing question..."):
                    first_question_prompt = f"""Ask the first {difficulty.lower()} difficulty {interview_type.lower()} interview question.
                    {f'Topic: {topic}' if topic else ''}
                    {'Provide the response in valid JSON format with fields: question (the interview question).' if structured_output else 'Just ask the question naturally.'}"""
                    
                    # API call with all tuned settings
                    response = openai.chat.completions.create(
                        model="gpt-4o-mini" if "mini" in model else "gpt-4" if "GPT-4o" in model else "gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": validated_prompt},
                            {"role": "user", "content": first_question_prompt}
                        ],
                        temperature=temperature,
                        top_p=top_p,
                        frequency_penalty=frequency_penalty
                    )
                    
                    # Track usage
                    input_tokens = response.usage.prompt_tokens
                    output_tokens = response.usage.completion_tokens
                    call_cost = calculate_cost(model, input_tokens, output_tokens)
                    st.session_state.total_tokens += input_tokens + output_tokens
                    st.session_state.total_cost += call_cost
                    
                    first_question = response.choices[0].message.content
                    st.markdown(first_question)
                    st.session_state.messages.append({"role": "assistant", "content": first_question})
    
    # Fixed chat input at bottom
    if prompt := st.chat_input("Type your answer here..."):
        # ===== SECURITY GUARD: Validate user input =====
        is_valid, validated_input = validate_input(prompt)
        if not is_valid:
            st.error(f"❌ Security check failed: {validated_input}")
            st.stop()
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": validated_input})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(validated_input)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Build context
                context = "\n".join([
                    f"{m['role']}: {m['content']}" 
                    for m in st.session_state.messages[-6:]
                ])
                
                # Get system prompt
                technique = PROMPT_TECHNIQUES[st.session_state.prompt_technique]
                system_prompt = technique["system_prompt"]
                
                # Validate system prompt
                is_valid, validated_prompt = validate_system_prompt(system_prompt)
                if not is_valid:
                    st.error(f"Security validation failed: {validated_prompt}")
                    st.stop()
                
                # Create prompt based on selected technique and output format
                if st.session_state.structured_output:
                    assistant_prompt = f"""The interview context:
{context}

Provide feedback on the answer and ask the next question.
Return your response as a valid JSON object with:
{{
    "score": integer 1-10,
    "strengths": [list of strengths],
    "improvements": [list of areas to improve],
    "next_question": "your next question",
    "evaluation": "detailed evaluation"
}}"""
                else:
                    assistant_prompt = f"""The interview context:
{context}

Provide feedback on the answer and ask the next question naturally.
Make it {difficulty.lower()} difficulty."""
                
                # API call with all tuned settings
                response = openai.chat.completions.create(
                    model="gpt-4o-mini" if "mini" in model else "gpt-4" if "GPT-4o" in model else "gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": validated_prompt},
                        {"role": "user", "content": assistant_prompt}
                    ],
                    temperature=temperature,
                    top_p=top_p,
                    frequency_penalty=frequency_penalty
                )
                
                # Track usage
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                call_cost = calculate_cost(model, input_tokens, output_tokens)
                st.session_state.total_tokens += input_tokens + output_tokens
                st.session_state.total_cost += call_cost
                
                assistant_response = response.choices[0].message.content
                
                # Display response based on format
                if st.session_state.structured_output:
                    try:
                        data = json.loads(assistant_response)
                        st.json(data)
                    except:
                        st.markdown(assistant_response)
                else:
                    st.markdown(assistant_response)
                
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
        
        st.rerun()

# Bottom padding
st.markdown("<div style='height: 100px'></div>", unsafe_allow_html=True)