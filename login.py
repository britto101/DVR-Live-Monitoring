import streamlit as st
from pathlib import Path


# ============================================================
# PAGE CONFIGURATION
# ============================================================

def configure_login_page():

    st.set_page_config(
        page_title="DVR Monitor",
        page_icon="📹",
        layout="centered",
        initial_sidebar_state="collapsed"
    )


# ============================================================
# LOGIN PAGE
# ============================================================

def login():

    # --------------------------------------------------------
    # Already logged in
    # --------------------------------------------------------

    if st.session_state.get("logged_in", False):
        return True


    # ========================================================
    # CUSTOM CSS
    # ========================================================

    st.markdown(
        """
        <style>

        /* ==================================================
           MAIN BACKGROUND
           ================================================== */

        [data-testid="stAppViewContainer"] {

            background:
                radial-gradient(
                    circle at 50% 45%,
                    #142b45 0%,
                    #0b192b 42%,
                    #050b14 100%
                ) !important;

            min-height: 100vh;
        }


        [data-testid="stHeader"] {
            background: transparent !important;
        }


        footer {
            display: none !important;
        }


        /* ==================================================
           REMOVE DEFAULT STREAMLIT SPACE
           ================================================== */

        .block-container {

            max-width: 100% !important;

            padding-top: 45px !important;

            padding-bottom: 45px !important;

            padding-left: 15px !important;

            padding-right: 15px !important;
        }


        /* ==================================================
           LOGIN CARD
           ================================================== */

        .login-card {

            width: 500px;

            max-width: 100%;

            margin: 0 auto;

            padding: 42px 44px 32px 44px;

            box-sizing: border-box;

            background:
                linear-gradient(
                    145deg,
                    rgba(25, 40, 58, 0.98),
                    rgba(12, 24, 39, 0.98)
                );

            border: 1px solid #176fd0;

            border-radius: 22px;

            box-shadow:
                0 30px 80px rgba(0, 0, 0, 0.55),
                0 0 50px rgba(0, 110, 255, 0.10);

        }


        /* ==================================================
           LOGO
           ================================================== */

        .logo-area {

            display: flex;

            justify-content: center;

            align-items: center;

            margin-bottom: 25px;
        }


        .logo-box {

            width: 110px;

            height: 110px;

            border-radius: 25px;

            background:
                linear-gradient(
                    145deg,
                    #1595ff,
                    #0668e8
                );

            border: 1px solid #42aaff;

            box-shadow:
                0 0 35px rgba(0, 130, 255, 0.38);

            display: flex;

            align-items: center;

            justify-content: center;

            overflow: hidden;

        }


        .logo-box img {

            width: 82px;

            height: 82px;

            object-fit: contain;

        }


        /* ==================================================
           TITLE
           ================================================== */

        .login-title {

            text-align: center;

            font-family:
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                Arial,
                sans-serif;

            font-size: 42px;

            font-weight: 700;

            line-height: 1.15;

            margin: 0;

            padding: 0;

            letter-spacing: -1px;

        }


        .dvr {

            color: #2196ff;

        }


        .monitor {

            color: #f5f7fb;

        }


        /* ==================================================
           SUBTITLE
           ================================================== */

        .login-subtitle {

            text-align: center;

            color: #94a8bf;

            font-family:
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                Arial,
                sans-serif;

            font-size: 15px;

            margin-top: 12px;

            margin-bottom: 34px;

        }


        /* ==================================================
           LABELS
           ================================================== */

        div[data-testid="stTextInput"] label {

            color: #f0f4f8 !important;

            font-size: 14px !important;

            font-weight: 600 !important;

            margin-bottom: 7px !important;

        }


        /* ==================================================
           INPUT CONTAINER
           ================================================== */

        div[data-testid="stTextInput"] {

            margin-bottom: 17px !important;

        }


        /* ==================================================
           INPUT
           ================================================== */

        div[data-testid="stTextInput"] input {

            height: 54px !important;

            background: #111d2b !important;

            color: #f4f7fb !important;

            border: 1px solid #41566e !important;

            border-radius: 10px !important;

            font-size: 15px !important;

            padding-left: 16px !important;

            padding-right: 16px !important;

            box-sizing: border-box !important;

        }


        /* Placeholder */

        div[data-testid="stTextInput"] input::placeholder {

            color: #7489a2 !important;

            opacity: 1 !important;

        }


        /* Focus */

        div[data-testid="stTextInput"] input:focus {

            border-color: #2196ff !important;

            box-shadow:
                0 0 0 1px #2196ff,
                0 0 18px rgba(33, 150, 255, 0.10) !important;

        }


        /* ==================================================
           PASSWORD EYE
           ================================================== */

        div[data-testid="stTextInput"] button {

            color: #9db0c5 !important;

            background: transparent !important;

            border: none !important;

        }


        /* ==================================================
           SIGN IN BUTTON
           ================================================== */

        div[data-testid="stFormSubmitButton"] {

            margin-top: 12px !important;

        }


        div[data-testid="stFormSubmitButton"] button {

            width: 100% !important;

            height: 58px !important;

            border-radius: 10px !important;

            border: 1px solid #39a5ff !important;

            background:
                linear-gradient(
                    90deg,
                    #1598ff,
                    #0869ed
                ) !important;

            color: #ffffff !important;

            font-size: 18px !important;

            font-weight: 600 !important;

            box-shadow:
                0 8px 25px rgba(0, 120, 255, 0.28) !important;

            transition: all 0.15s ease !important;

        }


        div[data-testid="stFormSubmitButton"] button:hover {

            background:
                linear-gradient(
                    90deg,
                    #25a4ff,
                    #0875f5
                ) !important;

            border-color: #4bb0ff !important;

            transform: translateY(-1px) !important;

            box-shadow:
                0 12px 30px rgba(0, 120, 255, 0.38) !important;

        }


        /* ==================================================
           ERROR
           ================================================== */

        div[data-testid="stAlert"] {

            margin-top: 16px !important;

            border-radius: 9px !important;

        }


        /* ==================================================
           SECURITY FOOTER
           ================================================== */

        .security-area {

            display: flex;

            align-items: center;

            justify-content: center;

            gap: 18px;

            margin-top: 31px;

        }


        .security-line {

            width: 75px;

            height: 1px;

            background: #34485e;

        }


        .security-text {

            color: #71869f;

            font-size: 12px;

            white-space: nowrap;

        }


        /* ==================================================
           MOBILE
           ================================================== */

        @media (max-width: 600px) {

            .block-container {

                padding-top: 25px !important;

                padding-left: 12px !important;

                padding-right: 12px !important;

            }


            .login-card {

                width: 100%;

                max-width: 500px;

                padding: 32px 24px 28px 24px;

                border-radius: 18px;

            }


            .logo-box {

                width: 92px;

                height: 92px;

                border-radius: 21px;

            }


            .logo-box img {

                width: 70px;

                height: 70px;

            }


            .login-title {

                font-size: 34px;

            }


            .login-subtitle {

                font-size: 13px;

                margin-bottom: 28px;

            }


            div[data-testid="stTextInput"] input {

                height: 50px !important;

            }


            div[data-testid="stFormSubmitButton"] button {

                height: 53px !important;

            }

        }

        </style>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # CAMERA IMAGE
    # ========================================================

    camera_path = Path(__file__).parent / "camera.png"


    # ========================================================
    # CENTER LOGIN CARD
    # ========================================================

    left_space, center, right_space = st.columns(
        [1, 2, 1],
        gap="small"
    )


    with center:

        # ----------------------------------------------------
        # CARD
        # ----------------------------------------------------

        st.markdown(
            '<div class="login-card">',
            unsafe_allow_html=True
        )


        # ----------------------------------------------------
        # CAMERA
        # ----------------------------------------------------

        if camera_path.exists():

            try:

                # Convert image to base64
                import base64

                with open(camera_path, "rb") as image_file:

                    image_data = base64.b64encode(
                        image_file.read()
                    ).decode("utf-8")


                image_html = f"""
                <div class="logo-area">

                    <div class="logo-box">

                        <img
                            src="data:image/png;base64,{image_data}"
                        >

                    </div>

                </div>
                """


                st.markdown(
                    image_html,
                    unsafe_allow_html=True
                )


            except Exception:

                st.markdown(
                    """
                    <div class="logo-area">

                        <div class="logo-box">

                            <div style="
                                font-size:45px;
                                line-height:1;
                            ">
                                📹
                            </div>

                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

        else:

            st.markdown(
                """
                <div class="logo-area">

                    <div class="logo-box">

                        <div style="
                            font-size:45px;
                            line-height:1;
                        ">
                            📹
                        </div>

                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )


        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        st.markdown(
            """
            <div class="login-title">

                <span class="dvr">
                    DVR
                </span>

                <span class="monitor">
                    Monitor
                </span>

            </div>
            """,
            unsafe_allow_html=True
        )


        # ----------------------------------------------------
        # SUBTITLE
        # ----------------------------------------------------

        st.markdown(
            """
            <div class="login-subtitle">
                Sign in to access the monitoring dashboard
            </div>
            """,
            unsafe_allow_html=True
        )


        # ====================================================
        # LOGIN FORM
        # ====================================================

        with st.form("login_form"):

            # ------------------------------------------------
            # USERNAME
            # ------------------------------------------------

            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                key="login_username"
            )


            # ------------------------------------------------
            # PASSWORD
            # ------------------------------------------------

            password = st.text_input(
                "Password",
                placeholder="Enter your password",
                type="password",
                key="login_password"
            )


            # ------------------------------------------------
            # SIGN IN
            # ------------------------------------------------

            login_button = st.form_submit_button(
                "Sign In  →",
                use_container_width=True
            )


            # =================================================
            # LOGIN VALIDATION
            # =================================================

            if login_button:

                try:

                    correct_username = st.secrets["USERNAME"]

                    correct_password = st.secrets["PASSWORD"]

                except Exception:

                    st.error(
                        "⚠️ Login credentials are not configured."
                    )

                    return False


                # ---------------------------------------------
                # CHECK LOGIN
                # ---------------------------------------------

                if (
                    username.strip() == correct_username
                    and password == correct_password
                ):

                    st.session_state["logged_in"] = True

                    st.session_state["username"] = (
                        username.strip()
                    )

                    st.rerun()


                else:

                    st.error(
                        "❌ Invalid username or password"
                    )


        # ====================================================
        # SECURITY FOOTER
        # ====================================================

        st.markdown(
            """
            <div class="security-area">

                <div class="security-line"></div>

                <div class="security-text">
                    Secure DVR Monitoring System
                </div>

                <div class="security-line"></div>

            </div>
            """,
            unsafe_allow_html=True
        )


        # ----------------------------------------------------
        # CLOSE CARD
        # ----------------------------------------------------

        st.markdown(
            "</div>",
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

        st.session_state.pop(
            "login_username",
            None
        )

        st.session_state.pop(
            "login_password",
            None
        )

        st.rerun()
