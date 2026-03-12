from __future__ import annotations
import json, os, time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from prompts_sabiox import SYSTEM_CHAT
from router import route
from local_help import answer_help
from gemini_client import gemini_chat, maybe_update_summary



def gemma_report(messages: List[Dict[str, str]]) -> str:
    for m in reversed(messages):
        if m.get("role") == "assistant":
            texto = m.get("content", "")
            # Procura por elementos que SEMPRE existem no seu relatório
            tem_identidade = "Projeto:" in texto or "### Especificação" in texto
            tem_proposito = "Purpose (REQ-PURP)" in texto or "1)" in texto
            
            if tem_identidade and tem_proposito:
                return texto
    return ""

def _history_dir() -> str:
    d = Path(__file__).resolve().parent / "historico_conversas"
    d.mkdir(parents=True, exist_ok=True)
    return str(d)

def _list_histories() -> List[str]:
    files = [f for f in os.listdir(_history_dir()) if f.endswith(".json")]
    files.sort(reverse=True)
    return files

def _save_history(payload: Dict[str, Any]) -> str:
    name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".json"
    path = os.path.join(_history_dir(), name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return name

def _load_history(filename: str) -> Dict[str, Any]:
    path = os.path.join(_history_dir(), filename)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {"messages": data, "summary": "", "last_report": ""}
    return {
        "messages": data.get("messages", []),
        "summary": data.get("summary", ""),
        "last_report": data.get("last_report", ""),
    }

def _delete_history(filename: str) -> None:
    path = os.path.join(_history_dir(), filename)
    if os.path.exists(path):
        os.remove(path)

def _init_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("summary", "")
    st.session_state.setdefault("last_report", "")
    st.session_state.setdefault("selected_history_file", "")

def _new_chat() -> None:
    st.session_state.messages = []
    st.session_state.summary = ""
    st.session_state.last_report = ""

def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown("# Menu")
        if st.button("Nova Conversa", use_container_width=True):
            _new_chat()
            st.rerun()

        if st.button("Salvar conversa", use_container_width=True):
            if not st.session_state.messages:
                st.warning("Nada para salvar.")
            else:
                name = _save_history({
                    "messages": st.session_state.messages,
                    "summary": st.session_state.summary,
                    "last_report": st.session_state.last_report,
                })
                st.success(f"Salvo: {name}")
            time.sleep(0.1)
            st.rerun()

        if st.button(" Enviar Relatório para Extração", use_container_width=True):
            if not st.session_state.messages:
                st.warning("A conversa ainda está vazia.")
            else:
                relatorio_texto = gemma_report(st.session_state.messages)
                if relatorio_texto:
                    st.session_state.last_report = relatorio_texto
                    st.success("Relatório capturado!")
                else:
                    st.error("Relatório não encontrado nas últimas mensagens.")
            time.sleep(1)
            st.rerun()

        st.subheader("Abrir histórico")
        files = _list_histories()
        if files:
            selected = st.selectbox("Selecione um arquivo:", files)
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Abrir", use_container_width=True):
                    st.session_state.update(_load_history(selected))
                    st.success("Carregado!")
                    time.sleep(0.1)
                    st.rerun()
            with col2:
                data = _load_history(selected)
                st.download_button(
                    "Download",
                    data=json.dumps(data, ensure_ascii=False, indent=2),
                    file_name=selected,
                    mime="application/json",
                    use_container_width=True,
                )
            with col3:
                if st.button("Excluir", type="primary", use_container_width=True):
                    _delete_history(selected)
                    st.toast(f"Arquivo deletado: {selected}")
                    time.sleep(0.1)
                    st.rerun()     

        # uploader de arquivos JSON
        st.markdown("### Carregar histórico")
        uploaded = st.file_uploader("Faça upload de um arquivo JSON", type="json", key="history_uploader")
        if uploaded:
            try:
                data = json.load(uploaded)
                name = _save_history(data)
                st.success(f"Histórico carregado: {name}")
                time.sleep(0.1)
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao carregar arquivo: {e}")

def _render_messages_with_delete() -> None:
    for idx, m in enumerate(st.session_state.messages):
        col1, col2 = st.columns([0.95, 0.05])
        with col1:
            st.chat_message(m["role"]).write(m["content"])
        with col2:
            if st.button("🗑️", key=f"del_{idx}"):
                st.session_state.messages.pop(idx)
                st.rerun()

def render_chat_page(settings: dict) -> None:
    _init_state()
    _render_sidebar()
    
    st.title("Chat – SABiOx")
    st.markdown("""
    **Bem-vindo ao Sistema SABiOx!**   
    Vamos criar uma ontologia!? Para começar envie uma mensagem contando um pouco sobre o projeto que você deseja criar. *Qual é o nome dele? Qual é a ideia principal?*
    <hr style="margin-top: 10px; margin-bottom: 5px; border: none; border-top: 1px solid rgba(128, 128, 128, 0.3);">
    """, unsafe_allow_html=True)
    
    if not settings.get("gemini_api_keys"):
        st.warning("Configure GEMINI_API_KEYS em Secrets/ENV.")
        st.stop()
    
    _render_messages_with_delete()

    user_input = st.chat_input("Digite sua mensagem…")
    if user_input:
        st.session_state.messages.append({"role":"user","content": user_input})

        mode = route(user_input)
        
        if mode == "HELP":
            help_text = answer_help(user_input)
            if help_text:
                st.session_state.messages.append({"role":"assistant","content": help_text})
                st.rerun()

        st.session_state.summary = maybe_update_summary(
            st.session_state.messages, st.session_state.summary,
            every_n_user_turns=int(settings.get("summary_every_n", 12))
        )

        with st.spinner("Respondendo…"):
            reply = gemini_chat(
                st.session_state.messages, 
                system_prompt=SYSTEM_CHAT, 
                summary=st.session_state.summary
            )
        st.session_state.messages.append({"role":"assistant","content": reply})
        st.rerun()