"""Shared CRUD state helpers for Streamlit pages."""
import streamlit as st


def _t(th: str, en: str) -> str:
    return th if st.session_state.get("lang", "TH") == "TH" else en


def init_crud_state(key: str) -> None:
    if f"{key}_mode" not in st.session_state:
        st.session_state[f"{key}_mode"] = "list"   # list | add | edit
    if f"{key}_edit_id" not in st.session_state:
        st.session_state[f"{key}_edit_id"] = None


def crud_toolbar(key: str, entity_th: str, entity_en: str) -> str:
    """Render Add / Back toolbar. Returns current mode."""
    mode = st.session_state.get(f"{key}_mode", "list")
    c1, c2 = st.columns([1, 8])
    if mode == "list":
        if c1.button("➕ " + _t(f"เพิ่ม{entity_th}", f"Add {entity_en}"), key=f"{key}_btn_add"):
            st.session_state[f"{key}_mode"] = "add"
            st.rerun()
    else:
        if c1.button("← " + _t("ย้อนกลับ", "Back"), key=f"{key}_btn_back"):
            st.session_state[f"{key}_mode"] = "list"
            st.session_state[f"{key}_edit_id"] = None
            st.rerun()
    return st.session_state.get(f"{key}_mode", "list")


def set_edit(key: str, row_id) -> None:
    st.session_state[f"{key}_mode"] = "edit"
    st.session_state[f"{key}_edit_id"] = str(row_id)
    st.rerun()


def set_list(key: str) -> None:
    st.session_state[f"{key}_mode"] = "list"
    st.session_state[f"{key}_edit_id"] = None
