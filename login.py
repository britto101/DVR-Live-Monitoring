import streamlit as st
from pathlib import Path

from PIL import Image


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
    # PAGE CSS
    # ========================================================

    st.markdown(
        """
        <style>

        /* ==================================================
           BACKGROUND
           ================================================== */

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(
                    circle at 50% 40%,
                    #182437 0%,
                    #101927 45%,
                    #080c13 100%
                );
            min-height: 100vh;
        }


        [data-testid="stHeader"] {
            background: transparent !important;
        }


        footer {
            display: none !important;
        }


        /* ==================================================
           MAIN AREA
           ================================================== */

        .block-container {
            max-width: 100% !important;

            padding-top: 0 !important;
            padding-bottom: 0 !important;

            padding-left: 0 !important;
            padding-right: 0 !important;
        }


        /* ==================================================
           LOGIN CARD
           ================================================== */

        div[data-testid="stForm"] {

            width: 430px !important;

            max-width: calc(100vw - 32px) !important;

            margin: 70px auto 0 auto !important;

            padding: 34px 38px 30px 38px !important;

            box-sizing: border-box !important;

            background:
                linear-gradient(
                    145deg,
                    #192535,
                    #101823
                ) !important;

            border: 1px solid #34465d !important;

            border-radius: 16px !important;

            box-shadow:
                0 25px 70px rgba(0, 0, 0, 0.60),
                0 0 40px rgba(20, 130, 255, 0.07) !important;
        }


        /* ==================================================
           LOGO CONTAINER
           ================================================== */

        .logo-box {

            width: 76px;
            height: 76px;

            margin: 0 auto 18px auto;

            border-radius: 18px;

            background:
                linear-gradient(
                    145deg,
                    #168cff,
                    #075bd6
                );

            border: 1px solid #3aa0ff;

            box-shadow:
                0 8px 28px rgba(0, 110, 255, 0.30);

            display: flex;

            align-items: center;
            justify-content: center;
        }


        /* ==================================================
           TITLE
           ================================================== */

        .title-dvr {

            text-align: center;

            color: #2196ff;

            font-size: 29px;

            font-weight: 700;

            line-height: 1.2;

            margin-top: 0;
            margin-bottom: 0;
        }


        .title-monitor {

            color: #f4f7fb;

            font-weight: 700;
        }


        /* ==================================================
           SUBTITLE
           ================================================== */

        .subtitle {

            text-align: center;

            color: #8996a9;

            font-size: 13.5px;

            margin-top: 8px;

            margin-bottom: 25px;
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
           INPUTS
           ================================================== */

        div[data-testid="stTextInput"] input {

            height: 46px !important;

            background: #141e2b !important;

            color: #f1f5f9 !important;

            border: 1px solid #3b4b61 !important;

            border-radius: 8px !important;

            font-size: 14px !important;

            padding-left: 13px !important;

            box-sizing: border-box !important;
        }


        div[data-testid="stTextInput"] input::placeholder {

            color: #68778b !important;

            opacity: 1 !important;
        }


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

            height: 47px !important;

            width: 100% !important;

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
                0 7px 20px rgba(0, 110, 255, 0.23) !important;

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

            transform: translateY(-1px);

            box-shadow:
                0 10px 26px rgba(0, 110, 255, 0.32) !important;
        }


        /* ==================================================
           ERROR
           ================================================== */

        div[data-testid="stAlert"] {

            margin-top: 15px !important;

            border-radius: 8px !important;
        }


        /* ==================================================
           FOOTER
           ================================================== */

        .secure-text {

            text-align: center;

            color: #667487;

            font-size: 11.5px;

            margin-top: 25px;
        }


        /* ==================================================
           MOBILE
           ================================================== */

        @media (max-width: 600px) {

            div[data-testid="stForm"] {

                width: calc(100vw - 28px) !important;

                margin-top: 30px !important;

                padding: 30px 24px 27px 24px !important;
            }

            .title-dvr {
                font-size: 26px;
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
    # LOGIN CARD
    # ========================================================

    with st.form("login_form"):

        # ----------------------------------------------------
        # CAMERA
        # ----------------------------------------------------

        if camera_path.exists():

            try:

                # Open image
                camera_image = Image.open(camera_path).convert("RGBA")

                # ------------------------------------------------
                # REMOVE WHITE BACKGROUND
                # ------------------------------------------------

                pixels = camera_image.load()

                width, height = camera_image.size

                for y in range(height):

                    for x in range(width):

                        r, g, b, a = pixels[x, y]

                        # Make white / near-white transparent
                        if (
                            r > 235
                            and g > 235
                            and b > 235
                        ):
                            pixels[x, y] = (
                                r,
                                g,
                                b,
                                0
                            )

                # ------------------------------------------------
                # CENTER LOGO
                # ------------------------------------------------

                logo_col1, logo_col2, logo_col3 = st.columns(
                    [1, 2, 1]
                )

                with logo_col2:

                    st.image(
                        camera_image,
                        width=72
                    )

            except Exception:

                # Fallback
                logo_col1, logo_col2, logo_col3 = st.columns(
                    [1, 2, 1]
                )

                with logo_col2:

                    st.markdown(
                        """
                        <div style="
                            width:72px;
                            height:72px;
                            margin:auto;
                            border-radius:18px;
                            background:linear-gradient(
                                145deg,
                                #168cff,
                                #075bd6
                            );
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            font-size:34px;
                        ">
                            📹
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        else:

            # ------------------------------------------------
            # IMAGE NOT FOUND
            # ------------------------------------------------

            logo_col1, logo_col2, logo_col3 = st.columns(
                [1, 2, 1]
            )

            with logo_col2:

                st.markdown(
                    """
                    <div style="
                        width:72px;
                        height:72px;
                        margin:auto;
                        border-radius:18px;
                        background:linear-gradient(
                            145deg,
                            #168cff,
                            #075bd6
                        );
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        font-size:34px;
                    ">
                        📹
                    </div>
                    """,
                    unsafe_allow_html=True
                )


        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        st.markdown(
            """
            <div class="title-dvr">
                DVR <span class="title-monitor">Monitor</span>
            </div>
            """,
            unsafe_allow_html=True
        )


        # ----------------------------------------------------
        # SUBTITLE
        # ----------------------------------------------------

        st.markdown(
            """
            <div class="subtitle">
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


        # ====================================================
        # LOGIN VALIDATION
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


            # ------------------------------------------------
            # SUCCESS
            # ------------------------------------------------

            if (
                username.strip() == correct_username
                and password == correct_password
            ):

                st.session_state["logged_in"] = True

                st.session_state["username"] = (
                    username.strip()
                )

                st.rerun()


            # ------------------------------------------------
            # WRONG LOGIN
            # ------------------------------------------------

            else:

                st.error(
                    "❌ Invalid username or password"
                )


        # ----------------------------------------------------
        # SECURITY TEXT
        # ----------------------------------------------------

        st.markdown(
            """
            <div class="secure-text">
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
