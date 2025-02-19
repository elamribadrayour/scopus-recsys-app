"""Password checking."""

import streamlit


def password_entered() -> None:
    """Checks whether a password entered by the user is correct."""
    data = streamlit.secrets["passwords"]
    username = streamlit.session_state["username"]
    password = streamlit.session_state["password"]
    if username in data and password == data[username]:
        streamlit.session_state["password_correct"] = True
        del streamlit.session_state["password"]  # don't store username + password
        del streamlit.session_state["username"]
    else:
        streamlit.session_state["password_correct"] = False


def is_password_ok() -> bool:
    """Returns `True` if the user had a correct password."""
    if "password_correct" not in streamlit.session_state:
        # First run, show inputs for username + password.
        streamlit.text_input("Username", on_change=password_entered, key="username")
        streamlit.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    if not streamlit.session_state["password_correct"]:
        # Password not correct, show input + error.
        streamlit.text_input("Username", on_change=password_entered, key="username")
        streamlit.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        streamlit.error("😕 User not known or password incorrect")
        return False

    # Password correct.
    return True
