import streamlit as st


# ============================================================
# LOGIN
# ============================================================

def login():

    # Already logged in
    if st.session_state.get("logged_in", False):
        return True

    st.set_page_config(
        page_title="DVR Monitor",
        page_icon="🔐",
        layout="centered"
    )

    # ========================================================
    # LOGIN PAGE CSS
    # ========================================================

    st.markdown(
        """
        <style>

        /* Remove default Streamlit top spacing */
        .block-container {
            padding-top: 3rem;
            padding-bottom: 2rem;
            max-width: 100%;
        }

        /* Main login area */
        .login-wrapper {
            width: 100%;
            max-width: 430px;
            margin: 70px auto 0 auto;
        }

        /* Login card */
        .login-card {
            background: #ffffff;
            border: 1px solid #e2e5e9;
            border-radius: 12px;
            padding: 38px 40px 34px 40px;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.07);
        }

        /* Logo */
        .login-logo {
            width: 58px;
            height: 58px;
            margin: 0 auto 18px auto;
            border-radius: 12px;
            background: #f0f4f8;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 29px;
        }

        /* Title */
        .login-title {
            text-align: center;
            font-size: 27px;
            font-weight: 700;
            color: #1f2937;
            margin: 0;
            padding: 0;
        }

        /* Subtitle */
        .login-subtitle {
            text-align: center;
            color: #6b7280;
            font-size: 14px;
            margin-top: 7px;
            margin-bottom: 28px;
        }

        /* Input labels */
        div[data-testid="stTextInput"] label {
            font-size: 14px;
            font-weight: 600;
            color: #374151;
        }

        /* Input boxes */
        div[data-testid="stTextInput"] input {
            height: 44px;
            border-radius: 7px;
            border: 1px solid #d1d5db;
            padding-left: 12px;
            font-size: 14px;
        }

        /* Input focus */
        div[data-testid="stTextInput"] input:focus {
            border-color: #2563eb;
            box-shadow: 0 0 0 1px #2563eb;
        }

        /* Login button */
        div[data-testid="stFormSubmitButton"] button {
            height: 44px;
            border-radius: 7px;
            background: #2563eb;
            border: 1px solid #2563eb;
            color: white;
            font-size: 15px;
            font-weight: 600;
            margin-top: 12px;
        }

        /* Login button hover */
        div[data-testid="stFormSubmitButton"] button:hover {
            background: #1d4ed8;
            border-color: #1d4ed8;
            color: white;
        }

        /* Footer */
        .login-footer {
            text-align: center;
            color: #9ca3af;
            font-size: 12px;
            margin-top: 22px;
        }

        /* Error message */
        div[data-testid="stAlert"] {
            border-radius: 7px;
            margin-top: 15px;
        }

        /* Sidebar logout button */
        section[data-testid="stSidebar"] button {
            border-radius: 7px;
        }

        </style>
        """,
        unsafe_allow_html=True
    )

    # ========================================================
    # LOGIN CARD
    # ========================================================

    st.markdown(
        """
        <div class="login-wrapper">

            <div class="login-card">

                <div class="login-logo">
                    🔐
                </div>

                <div class="login-title">
                    DVR Monitor
                </div>

                <div class="login-subtitle">
                    Sign in to access the monitoring dashboard
                </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    # ========================================================
    # LOGIN FORM
    # ========================================================

    with st.form("login_form"):

        username = st.text_input(
            "Username",
            placeholder="Enter your username",
            label_visibility="visible"
        )

        password = st.text_input(
            "Password",
            placeholder="Enter your password",
            type="password",
            label_visibility="visible"
        )

        login_button = st.form_submit_button(
            "Sign In",
            use_container_width=True
        )

    # ========================================================
    # CHECK LOGIN
    # ========================================================

    if login_button:

        try:
            correct_username = st.secrets["USERNAME"]
            correct_password = st.secrets["PASSWORD"]

        except Exception:
            st.error(
                "⚠️ Login credentials are not configured."
            )
            return False

        if (
            username.strip() == correct_username
            and password == correct_password
        ):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username.strip()

            st.rerun()

        else:
            st.error(
                "❌ Invalid username or password"
            )

    # ========================================================
    # FOOTER
    # ========================================================

    st.markdown(
        """
        <div class="login-footer">
            Secure DVR Monitoring System
        </div>
        """,
        unsafe_allow_html=True
    )

    return False


# ============================================================
# LOGOUT
# ============================================================

def logout():

    username = st.session_state.get(
        "username",
        "User"
    )

    st.sidebar.markdown("---")

    st.sidebar.markdown(
        f"👤 **{username}**"
    )

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):
        st.session_state["logged_in"] = False
        st.session_state.pop("username", None)

        st.rerun()
