import hashlib
import hmac
import re
import secrets
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

import streamlit as st


# ---------- PAGE SETTINGS ----------

st.set_page_config(
    page_title="Team Practice C",
    page_icon="✦",
    layout="wide",
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "accounts.db"
PASSWORD_ITERATIONS = 600_000


# ---------- DATABASE ----------

@contextmanager
def database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database():
    with database() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                phone TEXT NOT NULL DEFAULT '',
                address TEXT NOT NULL DEFAULT '',
                city TEXT NOT NULL DEFAULT '',
                country TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)


# ---------- PASSWORD HANDLING ----------

def hash_password(password):
    salt = secrets.token_bytes(16)

    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )

    return (
        f"pbkdf2_sha256${PASSWORD_ITERATIONS}$"
        f"{salt.hex()}${derived_key.hex()}"
    )


def verify_password(password, stored_hash):
    try:
        algorithm, iterations, salt, expected = stored_hash.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            int(iterations),
        )

        return hmac.compare_digest(actual.hex(), expected)
    except (ValueError, TypeError):
        return False


# ---------- ACCOUNT OPERATIONS ----------

def create_account(details, password):
    with database() as connection:
        connection.execute("""
            INSERT INTO accounts (
                first_name, last_name, email, username,
                password_hash, phone, address, city,
                country, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            details["first_name"],
            details["last_name"],
            details["email"],
            details["username"],
            hash_password(password),
            details["phone"],
            details["address"],
            details["city"],
            details["country"],
            datetime.now(timezone.utc).isoformat(),
        ))


# Used to perform a password check even when an email is unknown.
@st.cache_resource
def dummy_password_hash():
    return hash_password(secrets.token_urlsafe(32))


def authenticate(email, password):
    with database() as connection:
        account = connection.execute(
            "SELECT id, password_hash FROM accounts WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()

    stored_hash = (
        account["password_hash"] if account else dummy_password_hash()
    )
    password_matches = verify_password(password, stored_hash)

    if account and password_matches:
        return account["id"]

    return None


def get_profile(account_id):
    with database() as connection:
        return connection.execute("""
            SELECT first_name, last_name, email, username,
                   phone, address, city, country, created_at
            FROM accounts
            WHERE id = ?
        """, (account_id,)).fetchone()


# ---------- PAGE NAVIGATION ----------

def go_to(page):
    # Remove password widget values when switching pages.
    for key in list(st.session_state):
        if key.startswith(("login_", "signup_")):
            del st.session_state[key]

    st.session_state.page = page


def log_out():
    st.session_state.clear()
    st.session_state.page = "login"


# ---------- APPEARANCE ----------

st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(
            circle at 5% 10%,
            #e4dcff 0,
            transparent 38%
        ),
        radial-gradient(
            circle at 95% 90%,
            #f4dcf5 0,
            transparent 35%
        ),
        #f5f3ff;
}

.block-container {
    max-width: 1180px;
    padding-top: 2.5rem;
    padding-bottom: 3rem;
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
    color: #261447;
    font-size: 19px;
    font-weight: 800;
    margin-bottom: 36px;
}

.brand-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 42px;
    height: 42px;
    border-radius: 14px;
    background: #6d28d9;
    color: white;
    font-size: 27px;
}

.hero {
    padding: 34px 28px 30px 0;
}

.eyebrow {
    display: inline-block;
    padding: 7px 13px;
    border: 1px solid #d8ccfa;
    border-radius: 100px;
    color: #5b21b6;
    background: #ede9fe;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1.2px;
}

.hero h1 {
    margin-top: 22px;
    color: #261447;
    font-size: clamp(38px, 4.6vw, 62px);
    font-weight: 800;
    line-height: 1.08;
    letter-spacing: -2px;
}

.hero h1 span {
    color: #7c3aed;
}

.hero p {
    max-width: 410px;
    color: #655778;
    font-size: 17px;
    line-height: 1.8;
}

.feature {
    padding: 13px 0;
    color: #4d3a66;
    font-size: 15px;
}

.feature span {
    color: #7c3aed;
    font-weight: 800;
    margin-right: 10px;
}

.hero-note {
    margin-top: 35px;
    border-left: 3px solid #a78bfa;
    padding: 3px 0 3px 17px;
    color: #756387;
    font-size: 14px;
    line-height: 1.7;
}

[data-testid="stForm"] {
    padding: 30px;
    background: #ffffff;
    border: 1px solid #e6def5;
    border-radius: 24px;
    box-shadow: 0 18px 55px rgba(76, 29, 149, 0.08);
}

[data-testid="stForm"] h2 {
    color: #261447;
    letter-spacing: -0.8px;
}

[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    color: #261447;
}

[data-testid="stTextInput"] [data-baseweb="input"],
[data-testid="stTextArea"] [data-baseweb="textarea"] {
    background: #faf9ff;
    border-radius: 11px;
}

[data-testid="stTextInput"] [data-baseweb="input"]:focus-within,
[data-testid="stTextArea"] [data-baseweb="textarea"]:focus-within {
    border-color: #8b5cf6;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.13);
}

.stButton button,
.stFormSubmitButton button {
    min-height: 47px;
    border-radius: 11px;
    font-weight: 600;
    transition: background-color 0.2s ease, box-shadow 0.2s ease;
}

button[kind="primary"] {
    background: #6d28d9;
    border: 1px solid #6d28d9;
    color: white;
    box-shadow: 0 5px 15px rgba(109, 40, 217, 0.18);
}

button[kind="primary"]:hover {
    background: #5b21b6;
    border-color: #5b21b6;
    color: white;
}

button[kind="secondary"] {
    background: white;
    border: 1px solid #d8cced;
    color: #5b21b6;
}

button[kind="secondary"]:hover {
    background: #ede9fe;
    border-color: #a78bfa;
    color: #5b21b6;
}

button:focus-visible {
    outline: 3px solid #a78bfa;
    outline-offset: 3px;
}

.footer {
    text-align: center;
    color: #81728f;
    font-size: 12px;
    margin-top: 40px;
}

@media (max-width: 700px) {
    .block-container {
        padding: 1.5rem 1rem;
    }

    .hero {
        padding: 0 0 18px;
    }

    .hero h1 {
        font-size: 38px;
    }

    [data-testid="stForm"] {
        padding: 20px;
    }
}
</style>
""", unsafe_allow_html=True)


# ---------- INITIALIZATION ----------

initialize_database()

if "page" not in st.session_state:
    st.session_state.page = "login"

if "account_id" not in st.session_state:
    st.session_state.account_id = None

st.markdown("""
<div class="brand">
    <span class="brand-icon">✦</span>
    Team Practice C
</div>
""", unsafe_allow_html=True)

notice = st.session_state.pop("notice", None)
if notice:
    st.success(notice)


# ---------- DASHBOARD ----------

if st.session_state.account_id is not None:
    profile = get_profile(st.session_state.account_id)

    if profile is None:
        log_out()
        st.rerun()

    heading, action = st.columns([4, 1])

    with heading:
        st.caption("YOUR PERSONAL SPACE")
        st.title(f"Welcome, {profile['first_name']}!")
        st.write("Your account details, all in one place.")

    with action:
        st.button(
            "Log out",
            on_click=log_out,
            use_container_width=True,
        )

    st.divider()

    overview, contact = st.columns(2, gap="large")

    with overview:
        with st.container(border=True):
            st.subheader("Account details")
            st.text(
                f"Name: {profile['first_name']} "
                f"{profile['last_name']}"
            )
            st.text(f"Username: {profile['username']}")
            st.text(f"Email: {profile['email']}")
            st.text(f"Member since: {profile['created_at'][:10]}")

    with contact:
        with st.container(border=True):
            st.subheader("Contact details")

            for label, field in (
                ("Phone", "phone"),
                ("Address", "address"),
                ("City", "city"),
                ("Country", "country"),
            ):
                st.text(f"{label}: {profile[field] or 'Not provided'}")

    st.info("Your account has been saved in the local database.")


# ---------- LOGIN AND SIGNUP ----------

else:
    left, right = st.columns([1, 1.15], gap="large")

    with left:
        st.markdown("""
        <div class="hero">
            <div class="eyebrow">A SPACE TO CALL YOURS</div>
            <h1>Great things<br>start with<br><span>you.</span></h1>
            <p>
                Welcome to Team Practice C.
                Create your account and make yourself at home.
            </p>
            <div class="feature">
                <span>✦</span> A personal profile, in one place
            </div>
            <div class="feature">
                <span>✦</span> A simple way to get started
            </div>
            <div class="feature">
                <span>✦</span> Your space, ready when you are
            </div>
            <div class="hero-note">
                A fresh start. A little curiosity.<br>
                Something great to build together.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right:

        # ---------- LOGIN FORM ----------

        if st.session_state.page == "login":
            with st.form("login_form"):
                st.header("Welcome back")
                st.caption("Enter your details to access your account.")
                st.write("")

                email = st.text_input(
                    "Email address",
                    placeholder="you@example.com",
                    max_chars=254,
                    key="login_email",
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    max_chars=128,
                    key="login_password",
                )

                st.write("")

                submitted = st.form_submit_button(
                    "Log in →",
                    type="primary",
                    use_container_width=True,
                )

            if submitted:
                if not email.strip() or not password:
                    st.error("Enter both your email and password.")
                else:
                    with st.spinner("Checking your details..."):
                        account_id = authenticate(email, password)

                    if account_id is None:
                        st.error("Email or password is incorrect.")
                    else:
                        st.session_state.account_id = account_id
                        go_to("dashboard")
                        st.rerun()

            st.write("")
            st.caption("New here? Your account starts with a few details.")

            st.button(
                "Create an account",
                on_click=go_to,
                args=("signup",),
                use_container_width=True,
            )

        # ---------- SIGNUP FORM ----------

        else:
            with st.form("signup_form"):
                st.header("Create your account")
                st.caption("Make it yours. Fields marked * are required.")
                st.write("")

                st.markdown("**Personal details**")
                first, last = st.columns(2)

                with first:
                    first_name = st.text_input(
                        "First name *",
                        max_chars=80,
                        key="signup_first",
                    )

                with last:
                    last_name = st.text_input(
                        "Last name *",
                        max_chars=80,
                        key="signup_last",
                    )

                email = st.text_input(
                    "Email address *",
                    placeholder="you@example.com",
                    max_chars=254,
                    key="signup_email",
                )

                username = st.text_input(
                    "Username *",
                    placeholder="Choose a unique username",
                    help="3–40 letters, numbers, periods, underscores or hyphens.",
                    max_chars=40,
                    key="signup_username",
                )

                st.divider()
                st.markdown("**Account security**")
                st.caption("Choose a password with 15–128 characters.")

                password = st.text_input(
                    "Password *",
                    type="password",
                    max_chars=128,
                    key="signup_password",
                )

                confirm_password = st.text_input(
                    "Confirm password *",
                    type="password",
                    max_chars=128,
                    key="signup_confirm",
                )

                st.divider()

                with st.expander("Contact details · optional"):
                    phone = st.text_input(
                        "Phone number",
                        max_chars=30,
                        key="signup_phone",
                    )

                    address = st.text_area(
                        "Address",
                        max_chars=500,
                        key="signup_address",
                    )

                    city_column, country_column = st.columns(2)

                    with city_column:
                        city = st.text_input(
                            "City",
                            max_chars=100,
                            key="signup_city",
                        )

                    with country_column:
                        country = st.text_input(
                            "Country",
                            max_chars=100,
                            key="signup_country",
                        )

                st.write("")

                submitted = st.form_submit_button(
                    "Create account →",
                    type="primary",
                    use_container_width=True,
                )

            if submitted:
                details = {
                    "first_name": first_name.strip(),
                    "last_name": last_name.strip(),
                    "email": email.strip().lower(),
                    "username": username.strip(),
                    "phone": phone.strip(),
                    "address": address.strip(),
                    "city": city.strip(),
                    "country": country.strip(),
                }

                errors = []

                if not details["first_name"]:
                    errors.append("Enter your first name.")

                if not details["last_name"]:
                    errors.append("Enter your last name.")

                if not re.fullmatch(
                    r"[^\s@]+@[^\s@]+\.[^\s@]+",
                    details["email"],
                ):
                    errors.append("Enter a valid email address.")

                if not re.fullmatch(
                    r"[A-Za-z0-9_.-]{3,40}",
                    details["username"],
                ):
                    errors.append(
                        "Username must contain 3–40 letters, numbers, "
                        "periods, underscores or hyphens."
                    )

                if not 15 <= len(password) <= 128:
                    errors.append("Use a password with 15–128 characters.")

                if password != confirm_password:
                    errors.append("Your passwords do not match.")

                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    try:
                        with st.spinner("Creating your account..."):
                            create_account(details, password)
                    except sqlite3.IntegrityError:
                        st.error(
                            "An account already uses that email or username. "
                            "Try logging in or choose different details."
                        )
                    else:
                        go_to("login")
                        st.session_state.notice = (
                            "Your account was created. You can now log in."
                        )
                        st.rerun()

            st.write("")

            st.button(
                "← Back to login",
                on_click=go_to,
                args=("login",),
                use_container_width=True,
            )


# ---------- FOOTER ----------

st.markdown("""
<div class="footer">
    TEAM PRACTICE C · A little space for your next big beginning.
</div>
""", unsafe_allow_html=True)