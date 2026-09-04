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
# LOGIN
# ============================================================

def login():

    # --------------------------------------------------------
    # Already logged in
    # --------------------------------------------------------

    if st.session_state.get("logged_in", False):
        return True

    # --------------------------------------------------------
    # LOGIN PAGE CSS
    # --------------------------------------------------------

    st.markdown(
        """
        <style>

        /* ==================================================
           COMPLETE PAGE
           ================================================== */

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(
                    circle at 50% 40%,
                    #151d2b 0%,
                    #0d121b 48%,
                    #080b11 100%
                );
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        /* Hide Streamlit footer */
        footer {
            visibility: hidden;
        }

        /* Remove unnecessary top spacing */
        .block-container {
            max-width: 100% !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }


        /* ==================================================
           LOGIN CARD
           ================================================== */

        div[data-testid="stForm"] {

            width: 430px !important;

            max-width: calc(100vw - 30px) !important;

            margin: 75px auto 0 auto !important;

            padding: 34px 38px 30px 38px !important;

            box-sizing: border-box !important;

            background:
                linear-gradient(
                    145deg,
                    rgba(24, 32, 46, 0.98),
                    rgba(14, 20, 30, 0.98)
                ) !important;

            border: 1px solid #35445a !important;

            border-radius: 15px !important;

            box-shadow:
                0 22px 65px rgba(0, 0, 0, 0.55),
                0 0 35px rgba(0, 110, 255, 0.06) !important;
        }


        /* ==================================================
           CAMERA LOGO AREA
           ================================================== */

        .camera-logo {

            width: 72px;
            height: 72px;

            margin: 0 auto 18px auto;

            display: flex;

            align-items: center;

            justify-content: center;

            border-radius: 17px;

            background:
                linear-gradient(
                    145deg,
                    #168cff,
                    #075bd6
                );

            border: 1px solid #329dff;

            box-shadow:
                0 8px 28px rgba(0, 110, 255, 0.30);
        }

        .camera-logo img {

            width: 48px;
            height: 48px;

            object-fit: contain;

            display: block;
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
                sans-serif;

            font-size: 29px;

            font-weight: 700;

            line-height: 1.2;

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

            color: #8995a7;

            font-size: 13.5px;

            margin-top: 9px;

            margin-bottom: 27px;
        }


        /* ==================================================
           INPUT LABELS
           ================================================== */

        div[data-testid="stTextInput"] label {

            color: #d8dee8 !important;

            font-size: 13.5px !important;

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

            box-sizing: border-box !important;
        }

        div[data-testid="stTextInput"] input::placeholder {

            color: #687588 !important;

            opacity: 1 !important;
        }

        div[data-testid="stTextInput"] input:focus {

            border-color: #168cff !important;

            box-shadow:
                0 0 0 1px #168cff,
                0 0 12px rgba(22, 140, 255, 0.12) !important;
        }


        /* ==================================================
           LOGIN BUTTON
           ================================================== */

        div[data-testid="stFormSubmitButton"] {

            margin-top: 10px !important;
        }

        div[data-testid="stFormSubmitButton"] button {

            width: 100% !important;

            height: 47px !important;

            border-radius: 8px !important;

            border: 1px solid #168cff !important;

            background:
                linear-gradient(
                    90deg,
                    #168cff,
                    #0969e8
                ) !important;

            color: #ffffff !important;

            font-size: 15px !important;

            font-weight: 600 !important;

            box-shadow:
                0 7px 20px rgba(0, 110, 255, 0.22) !important;

            transition:
                transform 0.15s ease,
                box-shadow 0.15s ease !important;
        }

        div[data-testid="stFormSubmitButton"] button:hover {

            background:
                linear-gradient(
                    90deg,
                    #2196ff,
                    #0875f5
                ) !important;

            border-color: #2196ff !important;

            transform: translateY(-1px) !important;

            box-shadow:
                0 10px 26px rgba(0, 110, 255, 0.32) !important;
        }


        /* ==================================================
           FOOTER
           ================================================== */

        .login-footer {

            display: flex;

            align-items: center;

            justify-content: center;

            gap: 12px;

            margin-top: 26px;

            color: #687487;

            font-size: 11.5px;

            white-space: nowrap;
        }

        .login-footer::before,
        .login-footer::after {

            content: "";

            height: 1px;

            width: 55px;

            background: #293547;
        }


        /* ==================================================
           ERROR MESSAGE
           ================================================== */

        div[data-testid="stAlert"] {

            margin-top: 15px !important;

            border-radius: 8px !important;

            background: #28171b !important;

            border: 1px solid #71343d !important;

            color: #ffb4bd !important;
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

            .camera-logo {
                width: 64px;
                height: 64px;
            }

            .camera-logo img {
                width: 43px;
                height: 43px;
            }

            .login-footer::before,
            .login-footer::after {
                width: 35px;
            }
        }

        </style>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # CAMERA IMAGE
    # ========================================================

    camera_path = (
        Path(__file__).parent
        / "assets"
        / "camera.png"
    )


    # ========================================================
    # LOGIN CARD
    # ========================================================

    with st.form("login_form"):

        # ----------------------------------------------------
        # CAMERA LOGO
        # ----------------------------------------------------

        if camera_path.exists():

            with open(camera_path, "rb") as image_file:

                import base64

                image_base64 = base64.b64encode(
                    image_file.read()
                ).decode()

            st.markdown(
                f"""
                <div class="camera-logo">
                    <img
                        src="data:image/png;base64,{image_base64}"
                        alt="DVR Camera"
                    >
                </div>
                """,
                unsafe_allow_html=True
            )

        else:

            # Fallback if image is missing
            st.markdown(
                """
                <div class="camera-logo">
                    <span style="font-size:36px;">📹</span>
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
                <span class="dvr">DVR</span>
                <span class="monitor"> Monitor</span>
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


        # ----------------------------------------------------
        # USERNAME
        # ----------------------------------------------------

        username = st.text_input(
            "Username",
            placeholder="Enter your username"
        )


        # ----------------------------------------------------
        # PASSWORD
        # ----------------------------------------------------

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password"
        )


        # ----------------------------------------------------
        # SIGN IN
        # ----------------------------------------------------

        login_button = st.form_submit_button(
            "Sign In  →",
            use_container_width=True
        )


        # ----------------------------------------------------
        # LOGIN CHECK
        # ----------------------------------------------------

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

                st.session_state["username"] = (
                    username.strip()
                )

                st.rerun()

            else:

                st.error(
                    "❌ Invalid username or password"
                )


        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------

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

        st.session_state.pop(
            "username",
            None
        )

        st.rerun()
