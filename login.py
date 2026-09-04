import os
import streamlit as st
from dotenv import load_dotenv


# ============================================================
# LOAD .ENV
# ============================================================

load_dotenv()

LOGIN_USERNAME = "admin"
LOGIN_PASSWORD = "admin123"


# ============================================================
# LOGIN PAGE
# ============================================================

def login():

    # Already logged in
    if st.session_state.get("logged_in", False):
        return True

    st.set_page_config(
        page_title="DVR Monitor Login",
        page_icon="🔐",
        layout="centered"
    )

    # --------------------------------------------------------
    # CSS
    # --------------------------------------------------------

    st.markdown(
        """
        <style>

        .login-title {
            text-align: center;
            font-size: 32px;
            font-weight: 700;
            margin-top: 60px;
            margin-bottom: 30px;
        }

        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="login-title">🔐 DVR Monitor</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # LOGIN FORM
    # --------------------------------------------------------

    with st.form("login_form"):

        username = st.text_input(
            "Username",
            placeholder="Enter username"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter password"
        )

        login_button = st.form_submit_button(
            "LOGIN",
            use_container_width=True
        )

    # --------------------------------------------------------
    # CHECK LOGIN
    # --------------------------------------------------------

    if login_button:

        if not LOGIN_USERNAME or not LOGIN_PASSWORD:
            st.error("⚠️ Login credentials are not configured.")
            return False

        if (
            username.strip() == LOGIN_USERNAME
            and password == LOGIN_PASSWORD
        ):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username.strip()

            st.rerun()

        else:
            st.error("❌ Invalid username or password")

    return False


# ============================================================
# LOGOUT
# ============================================================

def logout():

    st.sidebar.markdown("---")

    username = st.session_state.get(
        "username",
        "User"
    )

    st.sidebar.write(f"👤 **{username}**")

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):
        st.session_state["logged_in"] = False
        st.session_state.pop("username", None)

        st.rerun()
