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


    # ========================================================
    # LOGIN PAGE CSS
    # ========================================================

    st.markdown(
        """
        <style>

        /* ==================================================
           PAGE BACKGROUND
           ================================================== */

        [data-testid="stAppViewContainer"] {

            background:
                radial-gradient(
                    circle at 50% 40%,
                    #192638 0%,
                    #101a29 45%,
                    #080c13 100%
                );

            min-height: 100vh;
        }


        /* Header */

        [data-testid="stHeader"] {
            background: transparent !important;
        }


        /* Hide footer */

        footer {
            display: none !important;
        }


        /* ==================================================
           MAIN CONTAINER
           ================================================== */

        .block-container {

            max-width: 100% !important;

            padding-top: 45px !important;

            padding-bottom: 40px !important;

            padding-left: 20px !important;

            padding-right: 20px !important;
        }


        /* ==================================================
           LOGIN CARD
           ================================================== */

        .login-card {

            width: 430px;

            max-width: 100%;

            margin: 25px auto 0 auto;

            padding: 35px 38px 30px 38px;

            box-sizing: border-box;

            background:
                linear-gradient(
                    145deg,
                    #192536,
                    #111a27
                );

            border: 1px solid #34465c;

            border-radius: 16px;

            box-shadow:
                0 25px 70px rgba(0, 0, 0, 0.60),
                0 0 35px rgba(20, 130, 255, 0.08);
        }


        /* ==================================================
           CAMERA AREA
           ================================================== */

        .camera-container {

            width: 76px;

            height: 76px;

            margin: 0 auto 18px auto;

            display: flex;

            align-items: center;

            justify-content: center;

            border-radius: 18px;

            background:
                linear-gradient(
                    145deg,
                    #168cff,
                    #075bd6
                );

            border: 1px solid #3aa0ff;

            box-shadow:
                0 8px 28px rgba(0, 110, 255, 0.28);

            overflow: hidden;
        }


        /* ==================================================
           TITLE
           ================================================== */

        .login-title {

            width: 100%;

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


        .dvr-text {
            color: #2196ff;
        }


        .monitor-text {
            color: #f5f7fb;
        }


        /* ==================================================
           SUBTITLE
           ================================================== */

        .login-subtitle {

            text-align: center;

            color: #8996a8;

            font-size: 13.5px;

            line-height: 1.5;

            margin-top: 9px;

            margin-bottom: 26px;
        }


        /* ==================================================
           INPUT LABEL
           ================================================== */

        div[data-testid="stTextInput"] label {

            color: #dce2ea !important;

            font-size: 13.5px !important;

            font-weight: 500 !important;
        }


        /* ==================================================
           INPUT BOX
           ================================================== */

        div[data-testid="stTextInput"] input {

            height: 46px !important;

            width: 100% !important;

            background: #141e2b !important;

            color: #f3f6fa !important;

            border: 1px solid #3b4c61 !important;

            border-radius: 8px !important;

            font-size: 14px !important;

            padding-left: 13px !important;

            box-sizing: border-box !important;
        }


        /* Placeholder */

        div[data-testid="stTextInput"] input::placeholder {

            color: #6d7b8e !important;

            opacity: 1 !important;
        }


        /* Focus */

        div[data-testid="stTextInput"] input:focus {

            border-color: #168cff !important;

            box-shadow:
                0 0 0 1px #168cff !important;
        }


        /* Password eye */

        div[data-testid="stTextInput"] button {

            color: #8b98aa !important;

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

            transition: all 0.15s ease !important;
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
                0 10px 26px rgba(0, 110, 255, 0.30) !important;
        }


        /* ==================================================
           ERROR MESSAGE
           ================================================== */

        div[data-testid="stAlert"] {

            margin-top: 15px !important;

            border-radius: 8px !important;
        }


        /* ==================================================
           SECURITY FOOTER
           ================================================== */

        .secure-text {

            text-align: center;

            color: #667488;

            font-size: 11.5px;

            margin-top: 25px;
        }


        /* ==================================================
           MOBILE
           ================================================== */

        @media (max-width: 600px) {

            .block-container {

                padding-top: 25px !important;

                padding-left: 14px !important;

                padding-right: 14px !important;
            }


            .login-card {

                width: 100%;

                max-width: 430px;

                margin-top: 15px;

                padding: 30px 24px 27px 24px;
            }


            .camera-container {

                width: 70px;

                height: 70px;
            }


            .login-title {

                font-size: 26px;
            }
        }

        </style>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # CENTER COLUMN
    #
    # This guarantees the entire login page is centered.
    # ========================================================

    left, center, right = st.columns(
        [1, 2, 1],
        gap="small"
    )


    # ========================================================
    # LOGIN CARD
    # ========================================================

    with center:

        st.markdown(
            """
            <div class="login-card">
            """,
            unsafe_allow_html=True
        )


        # ----------------------------------------------------
        # CAMERA IMAGE
        # ----------------------------------------------------

        camera_path = Path(__file__).parent / "camera.png"


        if camera_path.exists():

            # Use Streamlit image inside centered column
            image_col1, image_col2, image_col3 = st.columns(
                [1, 2, 1]
            )

            with image_col2:

                st.image(
                    str(camera_path),
                    width=72
                )

        else:

            st.markdown(
                """
                <div class="camera-container">
                    <span style="
                        font-size:34px;
                        line-height:1;
                    ">
                        📹
                    </span>
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
                <span class="dvr-text">DVR</span>
                <span class="monitor-text"> Monitor</span>
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
                placeholder="Enter your username"
            )


            # ------------------------------------------------
            # PASSWORD
            # ------------------------------------------------

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password"
            )


            # ------------------------------------------------
            # LOGIN BUTTON
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
                # SUCCESS
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


                # ---------------------------------------------
                # WRONG LOGIN
                # ---------------------------------------------

                else:

                    st.error(
                        "❌ Invalid username or password"
                    )


        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------

        st.markdown(
            """
            <div class="secure-text">
                Secure DVR Monitoring System
            </div>
            """,
            unsafe_allow_html=True
        )


        # Close card

        st.markdown(
            """
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
