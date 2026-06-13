import sys
import streamlit as st
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent / "src"))

from chain import run_pipeline
from memory import get_memory, reset_memory

# ════════════════════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="🎵 VibeCheck — Music Mood Recommender",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ════════════════════════════════════════════════════════════
# CSS — White Background, Black Text, Blue Accents
# ════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

    /* ── Global ── */
    .stApp {
        background-color: #f8f9ff;
        color: #111111;
        font-family: 'Space Grotesk', sans-serif;
    }

    /* ── Hide default streamlit chrome ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ── Navigation tabs ── */
    .nav-container {
        display: flex;
        gap: 12px;
        justify-content: center;
        margin: 20px 0 30px 0;
    }
    .nav-btn {
        background: #ffffff;
        border: 2px solid #2563eb;
        color: #2563eb;
        padding: 8px 28px;
        border-radius: 30px;
        font-weight: 600;
        font-size: 15px;
        cursor: pointer;
        transition: all 0.2s;
        text-decoration: none;
    }
    .nav-btn:hover, .nav-btn.active {
        background: #2563eb;
        color: #ffffff;
    }

    /* ── Hero section ── */
    .hero {
        text-align: center;
        padding: 50px 20px 30px 20px;
        background: linear-gradient(135deg, #eff6ff 0%, #f0f9ff 50%, #faf5ff 100%);
        border-radius: 24px;
        margin-bottom: 30px;
        border: 1px solid #dbeafe;
    }
    .hero h1 {
        font-size: 3.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #2563eb, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    .hero p {
        color: #64748b;
        font-size: 1.1rem;
        max-width: 500px;
        margin: 0 auto;
    }
    .hero .vibe-tag {
        display: inline-block;
        background: #eff6ff;
        color: #2563eb;
        border: 1px solid #bfdbfe;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
        margin: 4px;
    }

    /* ── Mood chips ── */
    .stButton > button {
        background: #ffffff !important;
        color: #2563eb !important;
        border: 2px solid #2563eb !important;
        border-radius: 30px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        padding: 8px 16px !important;
        transition: all 0.2s !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        background: #2563eb !important;
        color: #ffffff !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3) !important;
    }

    /* ── Search bar ── */
    .stTextInput > div > div > input {
        background: #ffffff;
        color: #111111;
        border: 2px solid #dbeafe;
        border-radius: 30px;
        padding: 14px 24px;
        font-size: 15px;
        font-family: 'Space Grotesk', sans-serif;
        box-shadow: 0 2px 10px rgba(37, 99, 235, 0.08);
    }
    .stTextInput > div > div > input:focus {
        border-color: #2563eb;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
    }

    /* ── Section headers ── */
    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #111111;
        margin: 24px 0 14px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* ── Song card ── */
    .song-card {
        background: #ffffff;
        border-radius: 20px;
        padding: 22px;
        margin: 14px 0;
        border: 1px solid #e0e7ff;
        box-shadow: 0 2px 12px rgba(37, 99, 235, 0.07);
        transition: all 0.25s;
    }
    .song-card:hover {
        box-shadow: 0 8px 30px rgba(37, 99, 235, 0.15);
        transform: translateY(-3px);
        border-color: #bfdbfe;
    }
    .song-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1e40af;
        margin: 0 0 4px 0;
    }
    .song-artist {
        color: #64748b;
        font-size: 0.95rem;
        margin: 0 0 12px 0;
    }
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin: 3px;
    }
    .badge-mood {
        background: #eff6ff;
        color: #2563eb;
        border: 1px solid #bfdbfe;
    }
    .badge-time {
        background: #f5f3ff;
        color: #7c3aed;
        border: 1px solid #ddd6fe;
    }
    .song-reason {
        color: #374151;
        font-size: 0.92rem;
        margin-top: 12px;
        line-height: 1.6;
        border-left: 3px solid #2563eb;
        padding-left: 12px;
    }

    /* ── Chat bubbles ── */
    .bubble-wrap { overflow: hidden; margin: 8px 0; }
    .user-bubble {
        background: linear-gradient(135deg, #2563eb, #7c3aed);
        color: #ffffff;
        padding: 10px 18px;
        border-radius: 20px 20px 4px 20px;
        display: inline-block;
        max-width: 65%;
        float: right;
        font-size: 0.9rem;
    }
    .dj-bubble {
        background: #f1f5f9;
        color: #111111;
        padding: 10px 18px;
        border-radius: 20px 20px 20px 4px;
        display: inline-block;
        max-width: 65%;
        float: left;
        font-size: 0.9rem;
        border: 1px solid #e2e8f0;
    }

    /* ── Playlist header ── */
    .playlist-header {
        background: linear-gradient(135deg, #eff6ff, #f5f3ff);
        border-radius: 16px;
        padding: 20px 24px;
        margin: 20px 0;
        border: 1px solid #dbeafe;
    }
    .playlist-header h3 {
        color: #1e40af;
        margin: 0 0 6px 0;
        font-size: 1.4rem;
    }
    .playlist-header p {
        color: #64748b;
        margin: 0;
        font-size: 0.9rem;
    }

    /* ── Error box ── */
    .error-box {
        background: #fff5f5;
        border: 1px solid #feb2b2;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        color: #c53030;
    }

    /* ── About page ── */
    .about-hero {
        background: linear-gradient(135deg, #eff6ff 0%, #f5f3ff 100%);
        border-radius: 24px;
        padding: 50px 40px;
        text-align: center;
        border: 1px solid #dbeafe;
        margin-bottom: 30px;
    }
    .about-hero h1 {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #2563eb, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 16px;
    }
    .about-hero p {
        color: #374151;
        font-size: 1.05rem;
        max-width: 600px;
        margin: 0 auto 20px auto;
        line-height: 1.7;
    }

    .team-card {
        background: #ffffff;
        border-radius: 20px;
        padding: 30px;
        text-align: center;
        border: 1px solid #e0e7ff;
        box-shadow: 0 2px 12px rgba(37, 99, 235, 0.07);
        transition: all 0.25s;
        height: 100%;
    }
    .team-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 35px rgba(37, 99, 235, 0.15);
    }
    .team-avatar {
        font-size: 4rem;
        margin-bottom: 16px;
    }
    .team-name {
        font-size: 1.3rem;
        font-weight: 700;
        color: #1e40af;
        margin-bottom: 6px;
    }
    .team-role {
        color: #7c3aed;
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 12px;
    }
    .team-desc {
        color: #64748b;
        font-size: 0.88rem;
        line-height: 1.6;
    }

    .fun-fact {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px 24px;
        border-left: 4px solid #2563eb;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.06);
    }
    .fun-fact h4 {
        color: #1e40af;
        margin: 0 0 6px 0;
        font-size: 1rem;
    }
    .fun-fact p {
        color: #374151;
        margin: 0;
        font-size: 0.9rem;
        line-height: 1.5;
    }

    .tech-pill {
        display: inline-block;
        background: #eff6ff;
        color: #2563eb;
        border: 1px solid #bfdbfe;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
        margin: 4px;
    }

    .divider-fancy {
        text-align: center;
        color: #94a3b8;
        font-size: 1.2rem;
        margin: 30px 0;
        letter-spacing: 8px;
    }

    /* ── Sidebar ── */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: #f8faff;
        border-right: 1px solid #dbeafe;
    }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# SESSION STATE
# ════════════════════════════════════════════════════════════
if "page" not in st.session_state:
    st.session_state.page = "home"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pipeline_result" not in st.session_state:
    st.session_state.pipeline_result = None


# ════════════════════════════════════════════════════════════
# NAVIGATION
# ════════════════════════════════════════════════════════════
col_nav1, col_nav2, col_nav3, col_nav4, col_nav5 = st.columns([2, 1, 1, 1, 2])
with col_nav2:
    if st.button("🎵 VibeCheck", key="nav_home"):
        st.session_state.page = "home"
        st.rerun()
with col_nav3:
    st.markdown("<div style='padding:8px 0; text-align:center; color:#94a3b8;'>|</div>",
                unsafe_allow_html=True)
with col_nav4:
    if st.button("👥 About Us", key="nav_about"):
        st.session_state.page = "about"
        st.rerun()


# ════════════════════════════════════════════════════════════
# ██████████ HOME PAGE ██████████
# ════════════════════════════════════════════════════════════
if st.session_state.page == "home":

    # ── Hero ──
    st.markdown("""
    <div class="hero">
        <h1>🎵 VibeCheck</h1>
        <p>Drop your mood. We drop the playlist.<br>
        No algorithm. Just pure vibe science. ✨</p>
        <br>
        <span class="vibe-tag">🧠 AI Powered</span>
        <span class="vibe-tag">🎯 Mood Matched</span>
        <span class="vibe-tag">⚡ Instant</span>
        <span class="vibe-tag">🎧 120 Songs</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Mood Chips ──
    st.markdown(
        '<div class="section-header">🎭 Pick your current vibe</div>',
        unsafe_allow_html=True
    )

    mood_chips = {
        "😢 Sad":         "sad heartbreak melancholic songs",
        "😊 Happy":       "happy upbeat feel good pop hits",
        "💪 Workout":     "motivational energetic workout songs",
        "🌧️ Rainy Day":  "rainy day chill melancholic music",
        "❤️ Romantic":    "romantic love songs",
        "🌙 Late Night":  "late night drive nostalgic songs",
        "😤 Angry":       "angry breakup energetic songs",
        "📚 Focus":       "focus study calm ambient music",
        "🎉 Party":       "party dance hits happy upbeat",
        "🎸 Indie":       "indie alternative rock nostalgic"
    }

    chip_query = None
    cols = st.columns(5)
    for i, (label, query) in enumerate(mood_chips.items()):
        with cols[i % 5]:
            if st.button(label, key=f"chip_{i}"):
                chip_query = query

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Search Bar ──
    st.markdown(
        '<div class="section-header">✍️ Or tell us exactly how you feel</div>',
        unsafe_allow_html=True
    )

    col_input, col_btn = st.columns([5, 1])
    with col_input:
        user_input = st.text_input(
            label="",
            placeholder="e.g. songs for crying at 3am with a cup of tea...",
            key="search_input",
            label_visibility="collapsed"
        )
    with col_btn:
        search_clicked = st.button("🔍 Find", use_container_width=True)

    # ── Determine Query ──
    final_query = None
    if chip_query:
        final_query = chip_query
    elif search_clicked and user_input.strip():
        final_query = user_input.strip()

    if "suggested_query" in st.session_state:
        final_query = st.session_state.pop("suggested_query")

    # ── Run Pipeline ──
    if final_query:
        with st.spinner("🎵 Scanning the vibes... hang tight!"):
            result = run_pipeline(final_query)
        st.session_state.pipeline_result = result

        if result["found"]:
            song_names = ", ".join([
                r["title"] for r in result["recommendations"]
            ])
            st.session_state.chat_history.append({
                "user": final_query,
                "dj":   f"Here are your songs: {song_names}"
            })
        else:
            st.session_state.chat_history.append({
                "user": final_query,
                "dj":   result["message"]
            })

    # ── Chat History ──
    if st.session_state.chat_history:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<div class="section-header">💬 Your Vibe History</div>',
            unsafe_allow_html=True
        )
        for exchange in st.session_state.chat_history[-3:]:
            st.markdown(f"""
            <div class="bubble-wrap">
                <div class="user-bubble">👤 {exchange["user"]}</div>
            </div>
            <div class="bubble-wrap">
                <div class="dj-bubble">🎧 {exchange["dj"]}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown(
            "<div style='clear:both; margin-bottom:20px;'></div>",
            unsafe_allow_html=True
        )

    # ── Results ──
    # ── Results ──
    if st.session_state.pipeline_result:
        result = st.session_state.pipeline_result

        if not result["found"]:
            st.markdown(f"""
            <div class="error-box">
                <h3>😕 Hmm, nothing matched that vibe</h3>
                <p>{result['message']}</p>
            </div>
            """, unsafe_allow_html=True)

            # ← YOUR ADDITION — Smart fallback suggestions (Feature 4)
            st.markdown(
                '<div class="section-header">💡 Try one of these instead</div>',
                unsafe_allow_html=True
            )
            suggestions = [
                "sad heartbreak songs",
                "upbeat happy songs",
                "calm study music",
                "late night drive",
                "angry breakup songs"
            ]
            s_cols = st.columns(len(suggestions))
            for i, suggestion in enumerate(suggestions):
                with s_cols[i]:
                    if st.button(suggestion, key=f"suggest_{i}"):
                        st.session_state["suggested_query"] = suggestion
                        st.rerun()

        else:
            recs = result["recommendations"]
            st.markdown(f"""
            <div class="playlist-header">
                <h3>🎧 Your {recs[0]['mood_match']} Playlist is Ready</h3>
                <p>
                    Based on → <b>"{result['query']}"</b> &nbsp;•&nbsp;
                    {len(recs)} handpicked songs &nbsp;•&nbsp;
                    Rewritten as → <i>"{result['rewritten_query']}"</i>
                </p>
            </div>
            """, unsafe_allow_html=True)

            # ← YOUR ADDITION — Analytics metrics (Feature 5)
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            with col_s1:
                st.metric("🎵 Songs Searched", "120")
            with col_s2:
                st.metric("🧩 Chunks Indexed", "441")
            with col_s3:
                st.metric("🔍 Retrieved", "10")
            with col_s4:
                st.metric("🎯 Final Picks", len(recs))

            # ← YOUR ADDITION — Rewrite toggle (Feature 6)
            show_rewrite = st.toggle("🔄 Show how AI interpreted your query")
            if show_rewrite and result.get("rewritten_query"):
                st.info(
                    f"**AI interpreted your mood as:** "
                    f"_{result['rewritten_query']}_"
                )

            for i, song in enumerate(recs):
                col_img, col_info = st.columns([1, 3])

                with col_img:
                    if song.get("cover_image"):
                        st.image(song["cover_image"], width=160)
                    else:
                        st.markdown("""
                        <div style="
                            width:160px; height:160px;
                            background:#eff6ff;
                            border-radius:16px;
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            font-size:56px;
                            border: 1px solid #dbeafe;
                        ">🎵</div>
                        """, unsafe_allow_html=True)

                with col_info:
                    st.markdown(f"""
                    <div class="song-card">
                        <div class="song-title">#{i+1} &nbsp; {song['title']}</div>
                        <div class="song-artist">🎤 {song['artist']}</div>
                        <span class="badge badge-mood">🎯 {song['mood_match']}</span>
                        <span class="badge badge-time">⏰ {song['best_time']}</span>
                        <div class="song-reason">{song['reason']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    track_id = song.get("track_id", "")
                    if track_id:
                        embed_url = (
                            f"https://open.spotify.com/embed/track/"
                            f"{track_id}?utm_source=generator&theme=0"
                        )
                        st.iframe(embed_url, height=80)
                    else:
                        st.caption("⚠️ No preview available")

                    hybrid_score = song.get("hybrid_score", None)
                    rerank_rank  = song.get("rerank_rank", i + 1)
                    energy       = song.get("energy", "")
                    if hybrid_score:
                        st.markdown(
                            f"<div style='font-size:11px; color:#94a3b8; "
                            f"margin-top:4px;'>"
                            f"📊 Hybrid Score: {hybrid_score:.3f} &nbsp;•&nbsp; "
                            f"⚡ Energy: {energy} &nbsp;•&nbsp; "
                            f"🏆 Rerank: #{rerank_rank}</div>",
                            unsafe_allow_html=True
                        )

                st.markdown("<br>", unsafe_allow_html=True)

            # RAG Debug Panel
            with st.expander("🔍 How the RAG Pipeline Found These Songs"):
                st.markdown("""
                **Pipeline executed in 8 steps:**

                1. ✅ Query rewritten into semantic description
                2. ✅ BM25 keyword search → 20 candidates
                3. ✅ ChromaDB semantic search → 20 candidates
                4. ✅ Hybrid merge (80% semantic + 20% BM25)
                5. ✅ Top 10 passed to LLM reranker
                6. ✅ Groq reranker selected top 3
                7. ✅ Context + memory injected into prompt
                8. ✅ Groq LLM generated personalized explanations
                """)
                st.markdown("**Raw LLM Output:**")
                st.code(result.get("raw_llm_response", ""), language="json")

    # ── Sidebar ──
    with st.sidebar:
        st.markdown("### 🎛️ Controls")
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.pipeline_result = None
            reset_memory()
            st.success("Vibes cleared!")
            st.rerun()

        st.markdown("---")
        st.markdown("### 📊 Session Stats")
        st.markdown(f"**Queries:** {len(st.session_state.chat_history)}")
        if st.session_state.pipeline_result:
            r = st.session_state.pipeline_result
            if r["found"]:
                st.markdown(f"**Last vibe:** {r['query']}")
                st.markdown(f"**Songs found:** {len(r['recommendations'])}")

        # Memory timeline
        st.markdown("---")
        st.markdown("### 🧠 Conversation Memory")
        memory = get_memory()
        if memory.is_empty():
            st.caption("No memory yet — start searching!")
        else:
            for idx, exchange in enumerate(memory.history, 1):
                st.markdown(
                    f"<div style='background:#eff6ff; border-radius:10px; "
                    f"padding:8px 12px; margin:6px 0; font-size:0.8rem; "
                    f"border-left:3px solid #2563eb;'>"
                    f"<b>Turn {idx}:</b> {exchange['user'][:40]}..."
                    f"</div>",
                    unsafe_allow_html=True
                )


# ════════════════════════════════════════════════════════════
# ██████████ ABOUT PAGE ██████████
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "about":

    # ── About Hero ──
    st.markdown("""
    <div class="about-hero">
        <h1>👋 Hey, we're VibeCheck!</h1>
        <p>
            Two data science students who got tired of spending 20 minutes
            choosing songs every time their mood shifted.<br><br>
            So we did what any slightly-unhinged CS student would do —
            we <b>built an AI to do it for us.</b> 🤓
        </p>
        <br>
        <span class="tech-pill">🐍 Python</span>
        <span class="tech-pill">🦜 LangChain</span>
        <span class="tech-pill">🗃️ ChromaDB</span>
        <span class="tech-pill">🤖 Groq LLM</span>
        <span class="tech-pill">🎵 Spotify API</span>
        <span class="tech-pill">🌀 Streamlit</span>
        <span class="tech-pill">📊 RAG Pipeline</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="divider-fancy">✦ ✦ ✦</div>',
        unsafe_allow_html=True
    )

    # ── Team Cards ──
    st.markdown(
        "<h2 style='text-align:center; color:#1e40af; margin-bottom:24px;'>"
        "🧑‍💻 The Masterminds Behind the Madness</h2>",
        unsafe_allow_html=True
    )

    col1, col_gap, col2 = st.columns([1, 0.1, 1])

    with col1:
        st.markdown("""
        <div class="team-card">
            <div class="team-avatar">👩‍💻</div>
            <div class="team-name">Ananya Manna</div>
            <div class="team-role">
                Data Science Noob · Stage 1 & 3 Architect
            </div>
            <div class="team-desc">
                Built the complete data ingestion pipeline — collecting
                120 songs across Spotify and syncedlyrics, cleaning
                lyrics, and assembling rich RAG documents. Designed
                the ChromaDB indexing strategy with 441 chunks and
                engineered the prompt templates and conversation memory
                system that powers every recommendation you see.<br><br>
                <b>Guilty pleasure:</b> Lo-fi beats at 2am while
                "studying" 🎧<br>
                <b>Mood RN:</b> Caffeinated and dangerous ☕
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="team-card">
            <div class="team-avatar">👨‍💻</div>
            <div class="team-name">Rajdeep Bose</div>
            <div class="team-role">
                Data Science Noob · Stage 2 & 4 Architect
            </div>
            <div class="team-desc">
                Built the complete retrieval pipeline — hybrid search
                combining BM25 keyword matching and ChromaDB semantic
                search, fused using weighted scoring. Designed the
                LLM-based reranker using Groq, structured output
                parsing with Pydantic, and the RAG chain that
                orchestrates all 8 pipeline stages from query to
                final recommendation.<br><br>
                <b>Guilty pleasure:</b> Hip-hop at full volume while
                coding 🎤<br>
                <b>Mood RN:</b> Quietly plotting world domination 🌍
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        '<div class="divider-fancy">✦ ✦ ✦</div>',
        unsafe_allow_html=True
    )

    # ── What is VibeCheck ──
    st.markdown(
        "<h2 style='text-align:center; color:#1e40af; margin-bottom:24px;'>"
        "🎵 What Even Is VibeCheck?</h2>",
        unsafe_allow_html=True
    )

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("""
        <div class="fun-fact">
            <h4>🧠 The Big Brain Idea</h4>
            <p>
                VibeCheck is a RAG (Retrieval Augmented Generation)
                powered music recommender. You tell it your mood,
                it searches through 120 carefully curated songs using
                a hybrid of keyword + semantic search, reranks them
                with an LLM, and serves you a playlist that actually
                matches your soul. No random shuffle. Pure vibe science.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="fun-fact">
            <h4>🔍 How It Actually Works</h4>
            <p>
                Your query → Query Rewriter (LLM expands it) →
                Hybrid Search (BM25 + ChromaDB vectors) →
                LLM Reranker (Groq picks the best) →
                Prompt Builder (injects context + memory) →
                Groq LLM generates recommendations →
                Structured output with reasons → You vibe. 🎉
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown("""
        <div class="fun-fact">
            <h4>📊 By The Numbers</h4>
            <p>
                🎵 <b>120 songs</b> in the catalog<br>
                🧩 <b>455 chunks</b> stored in ChromaDB<br>
                🎭 <b>15 mood categories</b> covered<br>
                🤖 <b>2 LLM calls</b> per query (rerank + generate)<br>
                💾 <b>5 exchange</b> conversation memory<br>
                ⚡ <b>~8 seconds</b> average response time
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="fun-fact">
            <h4>💡 Why We Built This</h4>
            <p>
                Semester 4, MAKAUT. We needed a project that was
                actually cool and not just another CRUD app.
                We wanted real RAG, real LLMs, real APIs —
                the whole shebang. Also we genuinely wanted
                something that could help us pick songs during
                exam season without losing 20 minutes of
                precious study time. Priorities. 📚🎵
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        '<div class="divider-fancy">✦ ✦ ✦</div>',
        unsafe_allow_html=True
    )

    # ── Message to Users ──
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #eff6ff, #f5f3ff);
        border-radius: 24px;
        padding: 40px;
        text-align: center;
        border: 1px solid #dbeafe;
        margin: 20px 0;
    ">
        <h2 style="color:#1e40af; margin-bottom:16px;">
            🎧 A Note From Us To You
        </h2>
        <p style="color:#374151; font-size:1.05rem;
                  max-width:600px; margin:0 auto; line-height:1.8;">
            Life's too short for bad playlists and random shuffles
            that somehow always pick the wrong song at the wrong time.
            <br><br>
            We built VibeCheck to be your personal mood DJ —
            one that actually <i>gets</i> you. Whether you're
            heartbroken at midnight, pumped for the gym, or just
            need something to match the rain outside your window,
            we've got you covered. 🌧️
            <br><br>
            <b>Now stop overthinking and go check your vibe. 🎵</b>
        </p>
        <br>
        <p style="color:#7c3aed; font-weight:600;">
            Made with ☕ + 🎧 + way too many late nights by
            Ananya & Rajdeep
        </p>
        <p style="color:#94a3b8; font-size:0.85rem;">
            Data Science Students · MAKAUT · Semester 4 · 2025
        </p>
    </div>
    """, unsafe_allow_html=True)