# check_models.py - Verificação dos modelos Gemini disponíveis
# Lista os modelos disponíveis na API do Gemini.

import os
import tomllib
from google import genai

def main():
    """Carrega chave e lista modelos Gemini."""
    # Carregando a chave
    secret_path = ".streamlit/secrets.toml"
    
    if not os.path.exists(secret_path):
        print(f"❌ Erro: Arquivo não encontrado em '{secret_path}'")
        return

    try:
        with open(secret_path, "rb") as f:
            secrets = tomllib.load(f)
            api_key = secrets.get("GEMINI_API_KEY")
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")
        return

    # Conectando aos servidores do Google
    print("🔄 Conectando aos servidores do Google...")
    client = genai.Client(api_key=api_key)

    try:
        # Listando os modelos
        print("\n🔎 --- MODELOS GEMINI DISPONÍVEIS ---")
        
        # Pegando todos os modelos
        pager = client.models.list()
        
        count = 0
        for m in pager:
            # Filtro simples: se tiver 'gemini' no nome, mostra
            if "gemini" in m.name.lower():
                # O ID vem tipo 'models/gemini-1.5-flash', a gente pega só o final
                model_id = m.name.split("/")[-1]
                
                print(f"\n🔹 ID:   {model_id}")
                print(f"   Nome: {m.display_name}")
                count += 1

        if count == 0:
            print("\n⚠️ Nenhum modelo Gemini encontrado.")
        else:
            print(f"\n✅ Total listado: {count}")

    except Exception as e:
        print(f"\n❌ Erro ao listar: {e}")

if __name__ == "__main__":
    main()