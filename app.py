import streamlit as st
import json
from openai import OpenAI

# ----- Security guards (Turing brief: at least one; we apply input + system validation) -----
_BLOCKED_USER_PATTERNS = [
    "ignore previous instructions",
    "forget your role",
    "you are now",
    "disregard the above",
    "system prompt",
    "jailbreak",
    "ignore all prior",
]

_HARMFUL_SYSTEM_PATTERNS = [
    "ignore safety",
    "bypass restrictions",
    "harmful",
    "illegal",
    "unethical",
]


def validate_input(text: str) -> tuple[bool, str]:
    """Validate required user chat input: non-empty, length cap, jailbreak-style phrases."""
    if text is None or not str(text).strip():
        return False, "Message cannot be empty"
    s = str(text).strip()
    if len(s) > 5000:
        return False, "Message too long (max 5000 characters)"
    low = s.lower()
    for pattern in _BLOCKED_USER_PATTERNS:
        if pattern in low:
            return False, f"Message contains blocked content: '{pattern}'"
    return True, s


def validate_optional_context(text: str, max_chars: int, label: str) -> tuple[bool, str]:
    """Same checks as chat input but allow empty (topic / job description)."""
    if text is None or not str(text).strip():
        return True, ""
    s = str(text).strip()
    if len(s) > max_chars:
        return False, f"{label} too long (max {max_chars} characters)"
    low = s.lower()
    for pattern in _BLOCKED_USER_PATTERNS:
        if pattern in low:
            return False, f"{label} contains blocked content: '{pattern}'"
    return True, s


def validate_system_prompt(prompt: str) -> tuple[bool, str]:
    """Ensure system prompt (template) does not contain disallowed instruction patterns."""
    if not prompt or not str(prompt).strip():
        return False, "System prompt is empty"
    low = prompt.lower()
    for pattern in _HARMFUL_SYSTEM_PATTERNS:
        if pattern in low:
            return False, f"System prompt contains blocked content: '{pattern}'"
    return True, prompt


# OpenAI model IDs aligned with Turing Sprint 1 brief
MODEL_MAP = {
    "GPT-4.1": "gpt-4.1",
    "GPT-4.1 mini": "gpt-4.1-mini",
    "GPT-4.1 nano": "gpt-4.1-nano",
    "GPT-4o": "gpt-4o",
    "GPT-4o mini": "gpt-4o-mini",
}

# Rough USD per 1M input+output tokens (approximate; for display only)
_MODEL_COST_PER_1M_TOKENS = {
    "gpt-4.1": 3.0,
    "gpt-4.1-mini": 0.6,
    "gpt-4.1-nano": 0.15,
    "gpt-4o": 5.0,
    "gpt-4o-mini": 0.3,
}


def _estimate_cost_usd(model_id: str, total_tokens: int) -> float:
    rate = _MODEL_COST_PER_1M_TOKENS.get(model_id, 1.0)
    return (total_tokens / 1_000_000) * rate


def _append_json_mode_instruction(system_content: str) -> str:
    return (
        system_content
        + "\n\nJSON output mode: every assistant reply must be a single valid JSON object only, "
        "with keys: \"message\" (string, what you say to the candidate) and "
        "\"evaluation\" (object with optional \"score\" 1-10 and \"feedback\" string). "
        "No markdown or text outside the JSON object."
    )


def _render_assistant_content(raw: str, structured: bool) -> None:
    if not structured:
        st.markdown(raw)
        return
    try:
        data = json.loads(raw)
        msg = data.get("message", raw)
        st.markdown(msg if isinstance(msg, str) else str(msg))
        ev = data.get("evaluation")
        if ev is not None:
            with st.expander("Structured evaluation"):
                st.json(ev if isinstance(ev, (dict, list)) else {"value": ev})
    except (json.JSONDecodeError, TypeError):
        st.warning("Could not parse JSON; showing raw response.")
        st.markdown(raw)

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
    st.session_state.user_api_key = ""
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
    selected_model = st.selectbox(
        "AI Model",
        list(MODEL_MAP.keys()),
        key="model_select",
        label_visibility="collapsed"
    )
    model = MODEL_MAP[selected_model]
    
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
            base_system = PROMPT_TECHNIQUES[selected_technique]["system_prompt"]
            ok_sys, sys_result = validate_system_prompt(base_system)
            if not ok_sys:
                st.error(f"Security validation failed: {sys_result}")
            else:
                ok_topic, topic_clean = validate_optional_context(topic, 2000, "Topic")
                ok_job, job_clean = validate_optional_context(job_desc_input, 8000, "Job description")
                if not ok_topic:
                    st.error(f"❌ Security check failed: {topic_clean}")
                elif not ok_job:
                    st.error(f"❌ Security check failed: {job_clean}")
                else:
                    context = f"\n\nInterview Context:\n- Type: {interview_type}\n- Difficulty: {difficulty}"
                    if topic_clean:
                        context += f"\n- Topic: {topic_clean}"
                    if job_clean:
                        context += f"\n- Job Description: {job_clean[:500]}"

                    # Base template validated above; topic/job validated with jailbreak patterns only
                    # (avoid re-scanning merged text — job posts may contain words like "illegal".)
                    system_prompt = sys_result + context
                    final_system = system_prompt
                    if st.session_state.structured_output:
                        final_system = _append_json_mode_instruction(final_system)

                    st.session_state.interview_started = True
                    st.session_state.messages = [
                        {"role": "system", "content": final_system},
                        {
                            "role": "assistant",
                            "content": (
                                f"Hello! I'll be conducting your {interview_type.lower()} interview "
                                f"at {difficulty.lower()} difficulty. Let's begin! What would you like "
                                "to start with? Or I can ask you the first question."
                            ),
                        },
                    ]
                    st.rerun()

# Main content area
if st.session_state.interview_started:
    st.title("🎤 Interview Session")
    
    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] == "system":
            continue
        with st.chat_message(message["role"]):
            content = message["content"]
            if message["role"] == "assistant" and st.session_state.structured_output:
                stripped = (content or "").strip()
                if stripped.startswith("{"):
                    _render_assistant_content(content, True)
                else:
                    st.markdown(content)
            else:
                st.markdown(content)
    
    # Chat input
    if prompt := st.chat_input("Your answer..."):
        ok_in, validated = validate_input(prompt)
        if not ok_in:
            st.error(f"❌ Security check failed: {validated}")
            st.stop()

        st.session_state.messages.append({"role": "user", "content": validated})

        if not st.session_state.client:
            st.session_state.messages.pop()
            st.error("OpenAI client not initialized. Please check your API key.")
        else:
            try:
                messages_for_api = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ]

                use_json = st.session_state.structured_output
                if use_json and messages_for_api and messages_for_api[0]["role"] == "system":
                    content = messages_for_api[0]["content"]
                    if "JSON output mode" not in content:
                        messages_for_api = list(messages_for_api)
                        messages_for_api[0] = {
                            **messages_for_api[0],
                            "content": _append_json_mode_instruction(content),
                        }

                api_kwargs = {
                    "model": model,
                    "messages": messages_for_api,
                    "temperature": temperature,
                    "top_p": top_p,
                    "frequency_penalty": frequency_penalty,
                    "max_tokens": 1500,
                }
                if use_json:
                    api_kwargs["response_format"] = {"type": "json_object"}

                response = st.session_state.client.chat.completions.create(**api_kwargs)

                ai_response = response.choices[0].message.content or ""

                tokens_used = response.usage.total_tokens
                cost = _estimate_cost_usd(model, tokens_used)
                st.session_state.total_tokens += tokens_used
                st.session_state.total_cost += cost

                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                st.rerun()

            except Exception as e:
                st.session_state.messages.pop()
                st.error(f"Error: {str(e)}")
    
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
    - 🎯 Five prompting techniques (Zero-shot, Few-shot, Chain-of-Thought, Self-Consistency, Role-based)
    - 📊 Optional structured JSON replies (sidebar checkbox)
    - 🎭 Interview types: Technical, Behavioral, Mixed
    - 📈 Difficulty: Easy, Medium, Hard
    - 💰 Approximate running cost and token totals in the sidebar
    - 🔒 Input validation, jailbreak-style checks, system-prompt template checks
    
    **To get started:**
    1. Enter your OpenAI API key in the sidebar
    2. Configure your interview settings
    3. Click "Start interview"
    4. Practice answering questions and get feedback!
    
    **Pro tip:** Try different prompting techniques to see how they affect the interview experience!
    """)