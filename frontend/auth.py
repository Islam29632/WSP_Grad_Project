import streamlit as st
import requests
import json


def login():
    st.title("Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        col1, col2 = st.columns(2)

        with col1:
            submit = st.form_submit_button("Login")
            if submit and username and password:
                try:
                    response = requests.post(
                        "http://localhost:8000/auth/token",
                        data={"username": username, "password": password},
                        timeout=5  # 5 seconds timeout
                    )

                    if response.status_code == 200:
                        token_data = response.json()
                        st.session_state["token"] = token_data["access_token"]
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = username
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        error_detail = "Invalid username or password"
                        try:
                            error_data = response.json()
                            if "detail" in error_data:
                                error_detail = error_data["detail"]
                        except:
                            pass
                        st.error(error_detail)
                except requests.ConnectionError:
                    st.error(
                        "Could not connect to the server. Please try again later.")
                except requests.Timeout:
                    st.error("Server request timed out. Please try again.")
                except Exception as e:
                    st.error(f"Login failed: {str(e)}")
            elif submit:
                st.warning("Please enter both username and password")

        with col2:
            if st.form_submit_button("Sign Up"):
                st.session_state["show_signup"] = True
                st.rerun()


def signup():
    st.title("Sign Up")

    with st.form("signup_form"):
        username = st.text_input("Username")
        st.markdown("""
        Password requirements:
        - At least 8 characters long
        - Contains at least one uppercase letter
        - Contains at least one lowercase letter
        - Contains at least one number
        - Contains at least one special character
        """)
        password = st.text_input("Password", type="password")
        password_confirm = st.text_input("Confirm Password", type="password")

        col1, col2 = st.columns(2)

        with col1:
            submit = st.form_submit_button("Create Account")
            if submit:
                if not username or not password or not password_confirm:
                    st.warning("Please fill in all fields")
                    return

                if password != password_confirm:
                    st.error("Passwords do not match")
                    return

                if len(username) < 3:
                    st.error("Username must be at least 3 characters long")
                    return

                try:
                    response = requests.post(
                        "http://localhost:8000/auth/signup",
                        json={"username": username, "password": password},
                        timeout=5
                    )

                    if response.status_code == 200:
                        st.success(
                            "Account created successfully! Please login.")
                        st.session_state["show_signup"] = False
                        st.rerun()
                    else:
                        error_detail = "Username already exists or invalid input"
                        try:
                            error_data = response.json()
                            if "detail" in error_data:
                                error_detail = error_data["detail"]
                        except:
                            pass
                        st.error(error_detail)
                except requests.ConnectionError:
                    st.error(
                        "Could not connect to the server. Please try again later.")
                except requests.Timeout:
                    st.error("Server request timed out. Please try again.")
                except Exception as e:
                    st.error(f"Registration failed: {str(e)}")

        with col2:
            if st.form_submit_button("Back to Login"):
                st.session_state["show_signup"] = False
                st.rerun()


def init_auth_state():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "token" not in st.session_state:
        st.session_state["token"] = None
    if "show_signup" not in st.session_state:
        st.session_state["show_signup"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = None


def logout():
    """Clear authentication state and token"""
    st.session_state["authenticated"] = False
    st.session_state["token"] = None
    st.session_state["username"] = None
    st.rerun()
