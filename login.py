import streamlit as st


# ============================================================
# LOGIN
# ============================================================

def login():

    # Already logged in
    if st.session_state.get("logged_in", False):
        return True

    # --------------------------------------------------------
    # PAGE CONFIG
    # --------------------------------------------------------

    st.set_page_config(
        page_title="DVR Monitor",
        page_icon="🔐",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    # --------------------------------------------------------
    # DARK LOGIN UI
    # --------------------------------------------------------

    st.markdown(
        """
        <style>

        /* ==================================================
           FULL PAGE BACKGROUND
           ================================================== */

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(
                    circle at center,
                    #151d2b 0%,
                    #0d121b 45%,
                    #080b11 100%
                );
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        /* Hide sidebar on login page */
        [data-testid="stSidebar"] {
            display: none;
        }

        /* Main content */
        .block-container {
            max-width: 100% !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }

        /* ==================================================
           LOGIN FORM / CARD
           ================================================== */

        div[data-testid="stForm"] {
            width: 430px !important;
            max-width: calc(100vw - 32px) !important;

            margin: 90px auto 0 auto !important;

            padding: 38px 38px 32px 38px !important;

            background:
                linear-gradient(
                    145deg,
                    rgba(24, 32, 46, 0.98),
                    rgba(15, 21, 31, 0.98)
                );

            border: 1px solid #35445a !important;
            border-radius: 14px !important;

            box-shadow:
                0 20px 60px rgba(0, 0, 0, 0.55),
                0 0 35px rgba(0, 110, 255, 0.06);

            box-sizing: border-box !important;
        }

        /* ==================================================
           LOGO
           ================================================== */

        .login-logo {
            width: 68px;
            height: 68px;

            margin: 0 auto 18px auto;

            display: flex;
            align-items: center;
            justify-content: center;

            border-radius: 16px;

            background:
                linear-gradient(
                    145deg,
                    #168cff,
                    #075bd6
                );

            border: 1px solid #329dff;

            box-shadow:
                0 8px 25px rgba(0, 110, 255, 0.30);

            font-size: 34px;
        }

        /* ==================================================
           TITLE
           ================================================== */

        .login-title {
            text-align: center;

            font-size: 29px;
            font-weight: 700;

            color: #f5f7fa;

            margin: 0;
            padding: 0;
        }

        .login-title .dvr {
            color: #2196ff;
        }

        .login-title .monitor {
            color: #f5f7fa;
        }

        /* ==================================================
           SUBTITLE
           ================================================== */

        .login-subtitle {
            text-align: center;

            font-size: 14px;

            color: #8995a7;

            margin-top: 8px;
            margin-bottom: 27px;
        }

        /* ==================================================
           LABELS
           ================================================== */

        div[data-testid="stTextInput"] label {
            color: #d7dde7 !important;

            font-size: 14px !important;
            font-weight: 500 !important;
        }

        /* ==================================================
           INPUT BOXES
           ================================================== */

        div[data-testid="stTextInput"] input {

            height: 46px !important;

            background: #151e2b !important;

            color: #eef2f7 !important;

            border: 1px solid #39485d !important;

            border-radius: 8px !important;

            font-size: 14px !important;

            padding-left: 13px !important;
        }

        /* Placeholder */

        div[data-testid="stTextInput"] input::placeholder {
            color: #697587 !important;
        }

        /* Input focus */

        div[data-testid="stTextInput"] input:focus {

            border-color: #168cff !important;

            box-shadow:
                0 0 0 1px #168cff,
                0 0 12px rgba(22, 140, 255, 0.12) !important;
        }

        /* ==================================================
           LOGIN BUTTON
           ================================================== */

        div[data-testid="stFormSubmitButton"] button {

            width: 100% !important;

            height: 47px !important;

            margin-top: 13px !important;

            border-radius: 8px !important;

            border: 1px solid #168cff !important;

            background:
                linear-gradient(
                    90deg,
                    #168cff,
                    #0969e8
                ) !important;

            color: white !important;

            font-size: 15px !important;

            font-weight: 600 !important;

            box-shadow:
                0 7px 20px rgba(0, 110, 255, 0.22) !important;

            transition: all 0.15s ease !important;
        }

        /* Button hover */

        div[data-testid="stFormSubmitButton"] button:hover {

            background:
                linear-gradient(
                    90deg,
                    #2196ff,
                    #0875f5
                ) !important;

            border-color: #2196ff !important;

            transform: translateY(-1px);

            box-shadow:
                0 9px 25px rgba(0, 110, 255, 0.32) !important;
        }

        /* ==================================================
           FOOTER
           ================================================== */

        .login-footer {

            display: flex;

            align-items: center;

            gap: 12px;

            margin-top: 28px;

            color: #687487;

            font-size: 12px;

            text-align: center;

            justify-content: center;
        }

        .login-footer::before,
        .login-footer::after {

            content: "";

            height: 1px;

            flex: 1;

            background: #293547;
        }

        /* ==================================================
           ERROR
           ================================================== */

        div[data-testid="stAlert"] {

            background: #28171b !important;

            border: 1px solid #71343d !important;

            color: #ffb4bd !important;

            border-radius: 8px !important;
        }

        /* ==================================================
           MOBILE
           ================================================== */

        @media (max-width: 600px) {

            div[data-testid="stForm"] {

                width: calc(100vw - 28px) !important;

                margin-top: 35px !important;

                padding: 30px 24px 27px 24px !important;
            }

            .login-title {
                font-size: 26px;
            }

            .login-logo {
                width: 62px;
                height: 62px;
            }
        }

        </style>
        """,
        unsafe_allow_html=True
    )

    # ========================================================
    # LOGIN CARD
    # ========================================================

    with st.form("login_form"):

        # Logo
        st.markdown(
            """
            <div class="login-logo">
                📹
            </div>
            """,
            unsafe_allow_html=True
        )

        # Title
        st.markdown(
            """
            <div class="login-title">
                <span class="dvr">DVR</span>
                <span class="monitor"> Monitor</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Subtitle
        st.markdown(
            """
            <div class="login-subtitle">
                Sign in to access the monitoring dashboard
            </div>
            """,
            unsafe_allow_html=True
        )

        # Username
        username = st.text_input(
            "Username",
            placeholder="Enter your username"
        )

        # Password
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password"
        )

        # Login button
        login_button = st.form_submit_button(
            "Sign In  →",
            use_container_width=True
        )

        # ====================================================
        # LOGIN CHECK
        # ====================================================

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

        # Footer
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

    st.sidebar.write(
        f"👤 **{username}**"
    )

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):

        st.session_state["logged_in"] = False

        st.session_state.pop(
            "username",
            None
        )

        st.rerun()
