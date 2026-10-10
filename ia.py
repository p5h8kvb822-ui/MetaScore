"""Appel à l'IA : clé OpenAI (ChatGPT) ou Anthropic, selon celle qui est configurée.
Secrets lus : OPENAI_API_KEY, sinon ANTHROPIC_API_KEY (une clé qui ne commence pas par « sk-ant » est traitée comme une clé OpenAI).
Modèle OpenAI modifiable avec la variable OPENAI_MODEL (défaut : gpt-4o)."""
import os
import requests


def disponible():
    return bool(os.getenv("OPENAI_API_KEY", "").strip() or os.getenv("ANTHROPIC_API_KEY", "").strip())


def demander(prompt, max_tokens=3000):
    """Texte de réponse de l'IA (lève une exception en cas d'erreur)."""
    cle_o = os.getenv("OPENAI_API_KEY", "").strip()
    cle_a = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not cle_o and cle_a and not cle_a.startswith("sk-ant"):
        cle_o, cle_a = cle_a, ""
    if cle_o:
        r = requests.post("https://api.openai.com/v1/chat/completions", timeout=180,
                          headers={"Authorization": f"Bearer {cle_o}", "Content-Type": "application/json"},
                          json={"model": os.getenv("OPENAI_MODEL", "").strip() or "gpt-4o",
                                "max_completion_tokens": max_tokens,
                                "messages": [{"role": "user", "content": prompt}]})
        if not r.ok:
            raise RuntimeError(f"OpenAI {r.status_code} : {r.text[:300]}")
        return r.json()["choices"][0]["message"]["content"]
    r = requests.post("https://api.anthropic.com/v1/messages", timeout=180,
                      headers={"x-api-key": cle_a, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                      json={"model": "claude-sonnet-5-5", "max_tokens": max_tokens,
                            "messages": [{"role": "user", "content": prompt}]})
    if not r.ok:
        raise RuntimeError(f"Anthropic {r.status_code} : {r.text[:300]}")
    return "".join(b.get("text", "") for b in r.json()["content"] if b.get("type") == "text")
