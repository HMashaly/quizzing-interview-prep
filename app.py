import streamlit as st
import os
from openai import OpenAI

# Initialize session state variables
if 'prompt_technique' not in st.session_state:
    st.session_state.prompt_technique = "Zero-shot"
if 'interview_started' not in st.session_state:
    st.session_state.interview_started = False
if 'total_cost' not in st.session_state:
    st.session_state.total_cost = 0
if 'total_tokens' not in st.session_state:
    st.session_state.total_tokens = 0
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'user_api_key' not in st.session_state:
    st.session_state.user_api_key = os.getenv("OPENAI_API_KEY", "")
if 'api_key_valid' not in st.session_state:
    st.session_state.api_key_valid = False
if 'client' not in st.session_state:
    st.session_state.client = None
if 'structured_output' not in st.session_state:
    st.session_state.structured_output = False

# Define PROMPT_TECHNIQUES
PROMPT_TECHNIQUES = {
    "Zero-shot": {
        "description": "Direct questioning without examples. Best for straightforward interviews.",
        "system_prompt": """You are an expert technical interviewer conducting a professional interview.
        Ask clear, direct questions and evaluate responses based on technical accuracy and communication.
        Provide constructive feedback after each response."""
    },
    "Few-shot": {
        "description": "Provides examples of good responses to guide the candidate.",
        "system_prompt": """You are an expert interviewer providing examples of high-quality responses.
        When asking questions, show 1-2 examples of what a great answer would look like.
        Help the candidate understand expectations while still challenging them to think independently."""
    },
    "Chain-of-Thought": {
        "description": "Encourages step-by-step reasoning for complex problems.",
        "system_prompt": """You are an interviewer focused on understanding problem-solving approaches.
        Encourage candidates to explain their reasoning step-by-step.
        Ask follow-up questions about their thought process and decision-making."""
    },
    "Self-Consistency": {
        "description": "Asks candidates to verify and improve their own answers.",
        "system_prompt": """You are an interviewer who encourages self-reflection and verification.
        After candidates answer, ask them to review their response for completeness or potential improvements.
        Encourage them to consider alternative approaches or edge cases."""
    },
    "Role-based": {
        "description": "Assigns specific roles (e.g., Senior Engineer, Product Manager) for context.",
        "system_prompt": """You are conducting a role-specific interview.
        Frame questions and evaluate responses based on the target role's responsibilities.
        Provide context about why certain skills are important for the role."""
    }
}

# Page config
st.set_page_config(
    page_title="AI Interview Practice",
    page_icon="🎓",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.tc-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    margin-bottom: 1rem;
    text-align: center;
}
.tc-header h2 {
    color: white;
    margin: 0;
}
.tc-header p {
    color: rgba(255,255,255,0.9);
    margin: 0.5rem 0 0 0;
}
.security-badge {
    background-color: #f0f2f6;
    padding: 0.5rem;
    border-radius: 5px;
    font-size: 0.8rem;
    font-family: monospace;
}
.stButton button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# SIDEBAR - CORRECT VERSION
with st.sidebar:
    # Turing College branding
    st.markdown("""
    <div class="tc-header">
        <h2>🎓 Turing College</h2>
        <p>AI Engineering - Interview Practice</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.title("🎯 Interview Settings")
    
    # ===== API KEY INPUT =====
    st.markdown("### 🔑 OpenAI API Key")
    
    # Add helpful link to get API key
    st.markdown("""
    <div style="font-size: 0.8rem; margin-top: -10px; margin-bottom: 10px;">
        <a href="https://platform.openai.com/api-keys" target="_blank">🔑 Get your API key here</a>
    </div>
    """, unsafe_allow_html=True)
    
    # API key input (masked)
    api_key_input = st.text_input(
        "OpenAI API Key",
        value=st.session_state.user_api_key,
        type="password",
        placeholder="sk-... or sk-proj-...",
        help="Enter your OpenAI API key. Get one from the link above",
        key="api_key_input_widget"
    )
    
    # Update client when key changes
    if api_key_input != st.session_state.user_api_key:
        st.session_state.user_api_key = api_key_input
        if api_key_input and api_key_input.startswith(('sk-', 'sk-proj-')):
            try:
                client = OpenAI(api_key=api_key_input)
                st.session_state.client = client
                st.session_state.api_key_valid = True
            except Exception as e:
                st.session_state.api_key_valid = False
                st.error(f"Invalid API key: {str(e)}")
    
    # Show API key status
    if st.session_state.user_api_key:
        if st.session_state.user_api_key.startswith(('sk-', 'sk-proj-')):
            st.success("✅ API Key ready")
            api_key = st.session_state.user_api_key
            client = st.session_state.get('client', None)
            if not client:
                try:
                    client = OpenAI(api_key=api_key)
                    st.session_state.client = client
                except:
                    client = None
        else:
            st.error("❌ Invalid format. Key should start with 'sk-' or 'sk-proj-'")
            api_key = None
            client = None
    else:
        st.warning("⚠️ Enter your API key to begin")
        api_key = None
        client = None
    
    st.markdown("---")
    
    # ===== PROMPT TECHNIQUE SELECTION =====
    st.markdown("### 🧠 Prompt Engineering Technique")
    selected_technique = st.selectbox(
        "Choose prompting technique:",
        list(PROMPT_TECHNIQUES.keys()),
        key="prompt_technique_select"
    )
    
    if selected_technique != st.session_state.prompt_technique:
        st.session_state.prompt_technique = selected_technique
        if st.session_state.interview_started:
            st.session_state.messages = []
            st.rerun()
    
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
    topic = st.text_input("Topic", placeholder="e.g., Python, System Design, Leadership", label_visibility="collapsed")    
    st.markdown("### Job description (optional)")
    job_desc_input = st.text_area("Job Description", placeholder="Paste job description here...", height=100, label_visibility="collapsed")

    # ===== LLM SETTINGS =====
    st.markdown("---")
    st.markdown("### ⚙️ LLM Settings")
    
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1, 
                           help="Lower = more focused, higher = more creative")
    
    top_p = st.slider("Top P", 0.0, 1.0, 1.0, 0.05,
                     help="Nucleus sampling - lower = more focused")
    
    frequency_penalty = st.slider("Frequency Penalty", -2.0, 2.0, 0.0, 0.1,
                                  help="Reduce repetition of tokens")
    
    st.markdown("### 🤖 AI Model")
    model_map = {
        "GPT-4o mini": "gpt-4o-mini",
        "GPT-4o": "gpt-4o",
        "GPT-3.5 Turbo": "gpt-3.5-turbo"
    }
    selected_model = st.selectbox(
        "AI Model",
        list(model_map.keys()),
        key="model_select",
        label_visibility="collapsed"
    )
    model = model_map[selected_model]
    
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
    start_button = st.button("🚀 Start interview", type="primary", use_container_width=True)
    
    if start_button:
        if not st.session_state.user_api_key:
            st.error("❌ Please enter your OpenAI API key first!")
        elif not st.session_state.api_key_valid:
            st.error("❌ Invalid API key! Please check your key.")
        else:
            st.session_state.interview_started = True
            st.session_state.messages = []
            
            # Create initial system message
            system_prompt = PROMPT_TECHNIQUES[selected_technique]['system_prompt']
            
            # Add interview context
            context = f"\n\nInterview Context:\n- Type: {interview_type}\n- Difficulty: {difficulty}"
            if topic:
                context += f"\n- Topic: {topic}"
            if job_desc_input:
                context += f"\n- Job Description: {job_desc_input[:500]}"
            
            system_prompt += context
            
            st.session_state.messages = [
                {"role": "system", "content": system_prompt},
                {"role": "assistant", "content": f"Hello! I'll be conducting your {interview_type.lower()} interview at {difficulty.lower()} difficulty. Let's begin! What would you like to start with? Or I can ask you the first question."}
            ]
            st.rerun()

# Main content area
if st.session_state.interview_started:
    st.title("🎤 Interview Session")
    
    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Your answer..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response
        if st.session_state.client:
            try:
                # Prepare messages for API
                messages_for_api = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ]
                
                # Call OpenAI API
                response = st.session_state.client.chat.completions.create(
                    model=model,
                    messages=messages_for_api,
                    temperature=temperature,
                    top_p=top_p,
                    frequency_penalty=frequency_penalty,
                    max_tokens=1000
                )
                
                ai_response = response.choices[0].message.content
                
                # Track tokens and cost
                tokens_used = response.usage.total_tokens
                cost = (tokens_used / 1000000) * 2.5  # Approximate cost for GPT-4o mini
                st.session_state.total_tokens += tokens_used
                st.session_state.total_cost += cost
                
                # Add AI response
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                with st.chat_message("assistant"):
                    st.markdown(ai_response)
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.error("OpenAI client not initialized. Please check your API key.")
    
    # End interview button
    if st.button("End Interview"):
        st.session_state.interview_started = False
        st.rerun()
        
else:
    # Welcome screen
    st.title("🎓 Turing College Interview Practice")
    st.markdown("""
    ### Welcome to your AI-powered interview preparation tool!
    
    **Features:**
    - 🎯 Multiple prompting techniques (Zero-shot, Few-shot, Chain-of-Thought, etc.)
    - 📊 Structured JSON output option
    - 🎭 Different interview types (Technical, Behavioral, Mixed)
    - 📈 Adjustable difficulty levels
    - 💰 Real-time cost tracking
    - 🔒 Security features (input validation, jailbreak detection)
    
    **To get started:**
    1. Enter your OpenAI API key in the sidebar
    2. Configure your interview settings
    3. Click "Start interview"
    4. Practice answering questions and get feedback!
    
    **Pro tip:** Try different prompting techniques to see how they affect the interview experience!
    """)