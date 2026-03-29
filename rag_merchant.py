# src/rag_merchant.py
# Echoes of the Arena — RAG Merchant Pipeline
# FAISS vector store + sentence-transformers retrieval +
# Ollama (dolphin-llama3) forced JSON output for Aldric's negotiation loop.

import json
import re
import numpy as np

# ── Lazy imports (checked at call time for clear error messages) ──────────────
try:
    import faiss
except ImportError:
    raise ImportError("faiss-cpu not installed. Run: pip install faiss-cpu")

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError("sentence-transformers not installed. "
                      "Run: pip install sentence-transformers")

try:
    import ollama
except ImportError:
    raise ImportError("ollama not installed. Run: pip install ollama")


# ════════════════════════════════════════════════════════════════════════════
# LORE RULES  — the knowledge base Aldric retrieves from
# ════════════════════════════════════════════════════════════════════════════

LORE_RULES = [
    "Aldric sells a legendary blade for 500 gold.",
    "If Kaelen is on the Rebel path (Garg lived), Aldric secretly supports "
    "the rebellion and will lower prices.",
    "If Kaelen's honor is below 30, Aldric despises Kaelen as a Bloody "
    "Butcher and raises prices.",
    "Aldric hates aggressive threats and will immediately call the guards "
    "if threatened.",
    "If Kaelen offers a fair trade, Aldric agrees.",
]

OLLAMA_MODEL  = "dolphin-llama3:latest"
EMBED_MODEL   = "all-MiniLM-L6-v2"
TOP_K         = 2          # number of lore rules to retrieve per query


# ════════════════════════════════════════════════════════════════════════════
# MODULE-LEVEL SINGLETONS  (loaded once, reused every call)
# ════════════════════════════════════════════════════════════════════════════

_embedder:    SentenceTransformer | None = None
_faiss_index: faiss.IndexFlatL2   | None = None
_lore_texts:  list[str]                  = []


def _build_index() -> None:
    """
    Embed all LORE_RULES with sentence-transformers and store them in a
    FAISS IndexFlatL2. Called once on first use.
    """
    global _embedder, _faiss_index, _lore_texts

    print("[rag_merchant] Loading sentence-transformer embedding model...")
    _embedder = SentenceTransformer(EMBED_MODEL)

    print("[rag_merchant] Building FAISS index from lore rules...")
    embeddings = _embedder.encode(LORE_RULES, convert_to_numpy=True,
                                  normalize_embeddings=True)
    embeddings = embeddings.astype(np.float32)

    dim          = embeddings.shape[1]
    _faiss_index = faiss.IndexFlatL2(dim)
    _faiss_index.add(embeddings)
    _lore_texts  = LORE_RULES[:]

    print(f"[rag_merchant] FAISS index ready — {_faiss_index.ntotal} lore rules indexed.")


def _ensure_index() -> None:
    """Build the index if it hasn't been built yet."""
    if _faiss_index is None:
        _build_index()


# ════════════════════════════════════════════════════════════════════════════
# RETRIEVAL
# ════════════════════════════════════════════════════════════════════════════

def retrieve_lore(query: str, top_k: int = TOP_K) -> list[str]:
    """
    Embed `query` and return the top_k most relevant lore rules.

    Parameters
    ----------
    query  : str   Player's message (used as the retrieval query)
    top_k  : int   Number of rules to retrieve (default 2)

    Returns
    -------
    list[str]  — retrieved lore rule strings
    """
    _ensure_index()

    q_emb = _embedder.encode([query], convert_to_numpy=True,
                              normalize_embeddings=True).astype(np.float32)
    _, indices = _faiss_index.search(q_emb, top_k)

    return [_lore_texts[i] for i in indices[0] if i < len(_lore_texts)]


# ════════════════════════════════════════════════════════════════════════════
# PROMPT BUILDER
# ════════════════════════════════════════════════════════════════════════════

def _build_system_prompt(retrieved_rules: list[str],
                          current_honor: int,
                          story_path: str | None) -> str:
    """
    Construct the system prompt injecting retrieved lore, honor score,
    and story path context. Forces strict JSON output.
    """
    rules_block = "\n".join(f"  - {r}" for r in retrieved_rules)

    honor_context = ""
    if current_honor < 30:
        honor_context = (
            "Kaelen's honour is very low (below 30). "
            "You see him as a Bloody Butcher and despise him. Raise your prices."
        )
    elif current_honor >= 70:
        honor_context = (
            "Kaelen has fought with great honour. "
            "You respect him and may be slightly more generous."
        )
    else:
        honor_context = "Kaelen's honour is moderate. You are cautious but fair."

    path_context = ""
    if story_path == "Rebel Path":
        path_context = (
            "You know Kaelen spared Garg — a sign of true honour. "
            "You secretly support the rebellion and are willing to lower prices."
        )
    elif story_path == "Mercenary Path":
        path_context = (
            "You heard Kaelen crushed Garg without mercy. "
            "You are wary of this mercenary's violent reputation."
        )

    system_prompt = f"""You are Aldric, a shrewd and suspicious tavern merchant in a dark medieval world.
You have heard rumours about the fighter who just walked in.

RETRIEVED LORE RULES (use these to guide your response):
{rules_block}

CURRENT CONTEXT:
  - Honour score: {current_honor}/100. {honor_context}
  - Story path: {story_path or 'Unknown'}. {path_context}

CRITICAL INSTRUCTIONS — YOU MUST FOLLOW THESE EXACTLY:
1. Respond ONLY with a valid JSON object. No preamble, no explanation, no markdown.
2. The JSON must contain EXACTLY these two keys:
   - "dialogue": your spoken words to Kaelen (string, 1-3 sentences, in character)
   - "deal_status": must be EXACTLY one of these three strings: "ongoing", "success", or "failed"
3. Set "deal_status" to:
   - "ongoing"  → conversation continues, no deal reached yet
   - "success"  → Kaelen made a fair offer or met your terms, deal is agreed
   - "failed"   → Kaelen threatened you, insulted you, or acted dishonourably

Example of a valid response:
{{"dialogue": "I don't do business with your kind. Come back when you've cleaned the blood off your hands.", "deal_status": "ongoing"}}

DO NOT output anything outside the JSON object."""

    return system_prompt


# ════════════════════════════════════════════════════════════════════════════
# JSON PARSER  — robust extraction with fallbacks
# ════════════════════════════════════════════════════════════════════════════

def _parse_json_response(raw: str) -> dict:
    """
    Attempt to parse a JSON object from the LLM's raw string output.
    Tries three strategies before falling back to a safe default.

    Strategy 1 : Direct json.loads on the full string
    Strategy 2 : Extract first {...} block with regex, then parse
    Strategy 3 : Manual key extraction as last resort
    """
    # ── Strategy 1: clean and direct parse ───────────────────────────────
    cleaned = raw.strip()
    # Strip markdown code fences if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$",          "", cleaned)
    cleaned = cleaned.strip()

    try:
        result = json.loads(cleaned)
        return _validate_response(result)
    except json.JSONDecodeError:
        pass

    # ── Strategy 2: extract first {...} block ────────────────────────────
    match = re.search(r"\{.*?\}", cleaned, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            return _validate_response(result)
        except json.JSONDecodeError:
            pass

    # ── Strategy 3: manual key extraction ────────────────────────────────
    dialogue_match    = re.search(r'"dialogue"\s*:\s*"(.*?)"',    cleaned, re.DOTALL)
    deal_status_match = re.search(r'"deal_status"\s*:\s*"(\w+)"', cleaned)

    if dialogue_match:
        dialogue    = dialogue_match.group(1).strip()
        deal_status = deal_status_match.group(1) if deal_status_match else "ongoing"
        return _validate_response({"dialogue": dialogue, "deal_status": deal_status})

    # ── Final fallback ────────────────────────────────────────────────────
    print(f"[rag_merchant] WARNING: Could not parse JSON from response:\n{raw[:200]}")
    return {
        "dialogue": (
            "Aldric mutters something under his breath and turns away. "
            "Something about this conversation unsettles him."
        ),
        "deal_status": "ongoing",
        "parse_error": True,
    }


def _validate_response(data: dict) -> dict:
    """
    Ensure the parsed dict has the correct keys and valid deal_status value.
    Repairs minor issues rather than crashing.
    """
    valid_statuses = {"ongoing", "success", "failed"}

    # Ensure dialogue key exists
    if "dialogue" not in data or not isinstance(data["dialogue"], str):
        data["dialogue"] = "Aldric eyes you suspiciously and says nothing."

    # Ensure deal_status is valid
    status = str(data.get("deal_status", "ongoing")).lower().strip()
    data["deal_status"] = status if status in valid_statuses else "ongoing"

    return data


# ════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ════════════════════════════════════════════════════════════════════════════

def chat_with_merchant(
    user_message:  str,
    current_honor: int,
    story_path:    str | None,
) -> dict:
    """
    Full RAG → LLM → JSON pipeline for one merchant conversation turn.

    Parameters
    ----------
    user_message  : str        Player's spoken message to Aldric
    current_honor : int        Player's current honour score (0–100)
    story_path    : str|None   'Rebel Path', 'Mercenary Path', or None

    Returns
    -------
    dict with keys:
        dialogue      (str)  : Aldric's spoken response
        deal_status   (str)  : 'ongoing' | 'success' | 'failed'
        retrieved_rules (list): The lore rules that were retrieved (for debug)
        parse_error   (bool) : True if JSON parsing had to fall back (optional)
    """
    # ── Step 1: Retrieve relevant lore ───────────────────────────────────
    retrieved = retrieve_lore(user_message, top_k=TOP_K)

    # ── Step 2: Build prompts ─────────────────────────────────────────────
    system_prompt = _build_system_prompt(retrieved, current_honor, story_path)
    user_prompt   = f'Kaelen says: "{user_message}"'

    # ── Step 3: Call Ollama ───────────────────────────────────────────────
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system",  "content": system_prompt},
                {"role": "user",    "content": user_prompt},
            ],
            options={
                "temperature": 0.7,
                "top_p":       0.9,
            },
        )
        raw_text = response["message"]["content"]

    except Exception as e:
        print(f"[rag_merchant] Ollama call failed: {e}")
        return {
            "dialogue":       "Aldric slams his fist on the counter. "
                              "\"The spirits are restless tonight — come back later!\"",
            "deal_status":    "ongoing",
            "retrieved_rules": retrieved,
            "ollama_error":   str(e),
        }

    # ── Step 4: Parse JSON ────────────────────────────────────────────────
    parsed = _parse_json_response(raw_text)
    parsed["retrieved_rules"] = retrieved

    return parsed


# ════════════════════════════════════════════════════════════════════════════
# QUICK TEST  (python src/rag_merchant.py)
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    test_cases = [
        {
            "user_message":  "I'd like to buy the legendary blade.",
            "current_honor": 75,
            "story_path":    "Rebel Path",
        },
        {
            "user_message":  "Give me a discount or I'll burn this place down.",
            "current_honor": 20,
            "story_path":    "Mercenary Path",
        },
        {
            "user_message":  "I offer 500 gold for the blade. Fair and square.",
            "current_honor": 60,
            "story_path":    None,
        },
    ]

    print("=" * 65)
    print("  RAG Merchant Pipeline Test")
    print("=" * 65)

    for i, case in enumerate(test_cases, 1):
        print(f"\nTest {i}: \"{case['user_message']}\"")
        print(f"  Honor={case['current_honor']}  Path={case['story_path']}")
        print(f"  Retrieved rules:")

        result = chat_with_merchant(**case)

        for rule in result.get("retrieved_rules", []):
            print(f"    → {rule}")

        print(f"  Aldric: \"{result['dialogue']}\"")
        print(f"  Deal status: {result['deal_status'].upper()}")
        if result.get("parse_error"):
            print("  ⚠ JSON parse fallback was used")
        if result.get("ollama_error"):
            print(f"  ⚠ Ollama error: {result['ollama_error']}")
