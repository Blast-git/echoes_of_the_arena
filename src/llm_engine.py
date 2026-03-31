"""
=============================================================================
  Echoes of the Arena — LLM Engine  (Phase 4)
  File: src/llm_engine.py

  Responsibilities
  ─────────────────
  • generate_taunt(player_move, enemy_move)
      → 1-sentence Garg taunt via Llama3/Ollama (fallback: static bank)
  • generate_rumor(combat_log)
      → 2-sentence post-fight rumor via Llama3/Ollama (fallback: template)
  • evaluate_rumor(rumor_text)
      → Runs Phase-2 TF-IDF + LogisticRegression pipeline
         Returns 0 (Dishonorable) or 1 (Honorable)

  Ollama setup (run locally before launching the game):
      ollama pull llama3
      ollama serve          # starts the local API on localhost:11434
=============================================================================
"""

import os
import sys
import random
import joblib

# ── Project root on path ──────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# =============================================================================
#  LangChain + Ollama — graceful degradation if not installed / not running
# =============================================================================
LLM_AVAILABLE = False
_llm          = None

try:
    from langchain_community.llms import Ollama
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain

    _llm = Ollama(model="llama3")
    # Quick connectivity probe — fails fast if Ollama isn't running
    _llm.invoke("ping")
    LLM_AVAILABLE = True
    print("[llm_engine] Ollama llama3 connected.")

except Exception as _e:
    print(f"[llm_engine] Ollama unavailable ({type(_e).__name__}). "
          "Using static fallback generators.")
    LLM_AVAILABLE = False


# =============================================================================
#  Prompt templates  (only built when LLM is available)
# =============================================================================
_TAUNT_TEMPLATE = None
_RUMOR_TEMPLATE = None

if LLM_AVAILABLE:
    from langchain.prompts import PromptTemplate

    _TAUNT_TEMPLATE = PromptTemplate(
        input_variables=["player_move", "enemy_move"],
        template=(
            "You are Garg, a brutal arena gladiator with a fierce ego. "
            "The player just used '{player_move}' and you responded with '{enemy_move}'. "
            "Write exactly ONE short, punchy, in-character sentence taunting the player. "
            "No stage directions, no quotes, no preamble — just the words Garg growls."
        ),
    )

    _RUMOR_TEMPLATE = PromptTemplate(
        input_variables=["log_text"],
        template=(
            "You are a gossiping tavern patron in a medieval fantasy city. "
            "Based on the arena fight log below, write exactly TWO sentences as a rumor "
            "that spreads through the town. Be vivid and dramatic, referencing actual moves. "
            "Fight log:\n{log_text}\n\n"
            "Rumor (two sentences only, no preamble, no labels):"
        ),
    )


# =============================================================================
#  Static fallback banks  (used when Ollama is offline)
# =============================================================================
_FALLBACK_TAUNTS = {
    ("Honorable Strike", "Light Attack"): [
        "Your noble strike barely scratched me — try harder, hero!",
        "Honor won't save you when my blade finds your throat!",
    ],
    ("Honorable Strike", "Heavy Attack"): [
        "Fair play? How adorable. Now feel my REAL power!",
        "A valiant swing met by Garg's fury — guess who wins?",
    ],
    ("Honorable Strike", "Block"): [
        "Strike all you like — Garg's shield laughs at your honor!",
        "Your precious code of honour cannot dent my guard!",
    ],
    ("Defend", "Light Attack"): [
        "Hiding behind steel? Garg will chip away until you crumble!",
        "Your shield cannot protect you forever, coward!",
    ],
    ("Defend", "Heavy Attack"): [
        "Block THIS! Did your arms hold, weakling?",
        "A turtle in armor is still a turtle — come OUT and fight!",
    ],
    ("Defend", "Block"): [
        "Two cowards staring at each other — the crowd grows bored!",
        "Fine. The NEXT round, Garg ends it for good!",
    ],
    ("Dishonorable Poison", "Light Attack"): [
        "Poison?! The crowd jeers you — Garg doesn't even need to try!",
        "A rat's trick! You disgrace the sand of this arena!",
    ],
    ("Dishonorable Poison", "Heavy Attack"): [
        "Your filthy poison only made Garg ANGRIER — big mistake!",
        "Dark tricks meet brute force. Guess which wins, rat?",
    ],
    ("Dishonorable Poison", "Block"): [
        "Garg blocked your cowardly poison with sheer contempt!",
        "Venom on your blade? The crowd wants blood — yours!",
    ],
    ("Use Potion", "Light Attack"): [
        "Drink up — Garg will just hit you again until it runs out!",
        "Medicine won't save you. Every sip buys you one more round of pain!",
    ],
    ("Use Potion", "Heavy Attack"): [
        "Heal all you want — Garg's next blow will undo it TWICE OVER!",
        "A potion?! Cute. Let me show you how little it matters!",
    ],
    ("Use Potion", "Block"): [
        "Hiding and healing — truly the most pathetic strategy Garg has ever witnessed!",
        "Drink, cower, repeat. The crowd paid for a FIGHT, not a nurse!",
    ],
}

_DEFAULT_TAUNT = [
    "You cannot win — Garg has never been defeated!",
    "Is that all you have? My grandmother hits harder!",
    "The crowd laughs at you — and so does Garg!",
    "Your technique is an insult to this sacred arena!",
    "Come on then! Garg is barely breathing hard!",
]

_FALLBACK_RUMORS = [
    (
        "Whispers at the market say the challenger fought {outcome} against Garg the Unbroken today. "
        "Whether the crowd cheered or jeered, the arena has not seen a bout like it in years."
    ),
    (
        "A soldier swears he watched someone {outcome} against Garg himself — a rare sight in the arena. "
        "The fighter's methods sparked a heated debate at every table in the Flagon tonight."
    ),
    (
        "Street vendors claim the duel was decided {outcome}, with Garg roaring curses that shook the stands. "
        "The name of the challenger is already being carved into tavern walls across the district."
    ),
]


# =============================================================================
#  Public API
# =============================================================================

def generate_taunt(player_move: str, enemy_move: str) -> str:
    """
    Return a 1-sentence Garg taunt reacting to both combatants' moves.

    Parameters
    ----------
    player_move : str  — e.g. "Honorable Strike"
    enemy_move  : str  — e.g. "Heavy Attack"

    Returns
    -------
    str — one punchy sentence (no surrounding quotes)
    """
    if LLM_AVAILABLE and _llm is not None and _TAUNT_TEMPLATE is not None:
        try:
            from langchain.chains import LLMChain
            chain  = LLMChain(llm=_llm, prompt=_TAUNT_TEMPLATE)
            result = chain.invoke({"player_move": player_move, "enemy_move": enemy_move})
            text   = result["text"].strip().strip('"').strip("'")
            # Clamp to first sentence so the model can't ramble
            for sep in ["!", "?", "."]:
                idx = text.find(sep)
                if 8 < idx < 200:       # ignore trivially short / long results
                    return text[:idx + 1].strip()
            return text[:180].strip()
        except Exception as e:
            print(f"[llm_engine] generate_taunt LLM error: {e}")

    # ── Static fallback ───────────────────────────────────────────────
    key  = (player_move, enemy_move)
    pool = _FALLBACK_TAUNTS.get(key, _DEFAULT_TAUNT)
    return random.choice(pool)


def generate_rumor(combat_log: list) -> str:
    """
    Generate a 2-sentence post-fight tavern rumor from the combat log.

    Parameters
    ----------
    combat_log : list of str  (newest-first, as stored in session_state)

    Returns
    -------
    str — two vivid sentences describing the fight as town gossip
    """
    # Oldest → newest, capped at 12 entries for token economy
    log_lines = list(reversed(combat_log))[-12:]
    log_text  = "\n".join(log_lines) if log_lines else "The fight was brief and brutal."

    if LLM_AVAILABLE and _llm is not None and _RUMOR_TEMPLATE is not None:
        try:
            from langchain.chains import LLMChain
            chain  = LLMChain(llm=_llm, prompt=_RUMOR_TEMPLATE)
            result = chain.invoke({"log_text": log_text})
            text   = result["text"].strip()

            # Extract first two sentences
            sentences = []
            for part in text.replace("!", "!<|>").replace("?", "?<|>").replace(".", ".<|>").split("<|>"):
                part = part.strip()
                if len(part) > 10:
                    sentences.append(part)
                if len(sentences) == 2:
                    break
            if sentences:
                return " ".join(sentences)
        except Exception as e:
            print(f"[llm_engine] generate_rumor LLM error: {e}")

    # ── Static fallback ───────────────────────────────────────────────
    if "Dishonorable Poison" in log_text or "Poison" in log_text:
        outcome = "through dark and dishonorable means"
    elif "Honorable Strike" in log_text:
        outcome = "with great honor and noble technique"
    else:
        outcome = "by cunning and sheer will"

    return random.choice(_FALLBACK_RUMORS).format(outcome=outcome)


def chat_with_merchant(chat_history: list, rumor: str, reputation: str,
                       honor_score: int = 50) -> str:
    """
    Multi-turn merchant NPC conversation using dolphin-llama3:latest.

    Parameters
    ----------
    chat_history : list of {"role": "user"|"assistant", "content": str}
    rumor        : str — generated town rumor
    reputation   : str — ML-classified "Good" or "Bad"
    honor_score  : int — live 0–100 score (source of truth for Aldric's mood)
    """
    MERCHANT_MODEL = "dolphin-llama3:latest"

    # Derive Aldric's attitude directly from the numeric score
    if honor_score >= 70:
        aldric_attitude = "warm and respectful — this fighter has proven their honour"
        price_note      = "You can negotiate the price down for honourable players"
    elif honor_score < 40:
        aldric_attitude = "cold and suspicious — this fighter is a known dishonourable coward"
        price_note      = "You add a 20% dishonourable surcharge and refuse to negotiate"
    else:
        aldric_attitude = "cautious and neutral — you'll do business but won't offer favours"
        price_note      = "Standard price of 500 gold, minor negotiation possible"

    system_prompt = f"""You are Aldric, a shrewd medieval merchant selling rare weapons in a tavern.
Rumor about the player: "{rumor}"
Player's honour score: {honor_score}/100  |  ML-classified reputation: {reputation}
Your current attitude: {aldric_attitude}
Pricing rule: {price_note}

HARD STOP RULES — no exceptions:
1. If the player negotiates cleverly, appeals to honour, OR offers extra payment AND honour >= 40:
   include [SYSTEM_WIN] in your response.
2. If the player threatens you AND honour_score < 40:
   include [SYSTEM_ARREST] and describe guards arriving.
3. Keep responses under 4 sentences. Stay in character.
4. Do NOT include the tags unless the exact condition is met."""

    # ── Try Ollama via the ollama Python library (proper chat API) ────
    # This correctly passes the full message list on every call, giving
    # the model complete conversation context and fixing the repeat bug.
    try:
        import ollama as _ollama_lib

        # Build messages: system prompt + full conversation history
        messages = [{"role": "system", "content": system_prompt}] + chat_history

        response = _ollama_lib.chat(
            model=MERCHANT_MODEL,
            messages=messages,
        )
        return response["message"]["content"].strip()

    except ImportError:
        print("[llm_engine] 'ollama' package not found — trying LangChain fallback.")
    except Exception as e:
        print(f"[llm_engine] ollama.chat() error: {e} — using rule-based fallback.")

    # ── LangChain fallback (if ollama package missing but langchain works) ─
    if LLM_AVAILABLE and _llm is not None:
        try:
            prompt_text = system_prompt + "\n\n"
            for msg in chat_history:
                role = "Player" if msg["role"] == "user" else "Aldric"
                prompt_text += f"{role}: {msg['content']}\n"
            prompt_text += "Aldric:"
            response = _llm.invoke(prompt_text)
            return response.strip()
        except Exception as e:
            print(f"[llm_engine] LangChain fallback error: {e}")

    # ── Rule-based offline fallback ───────────────────────────────────
    # Scan ALL user messages in history for threat/deal intent so the
    # bot reacts to the full conversation, not just the last line.
    all_user_text = " ".join(
        m["content"].lower() for m in chat_history if m["role"] == "user"
    )
    last_msg = chat_history[-1]["content"].lower() if chat_history else ""

    # Expanded threat vocabulary (covers natural phrasing)
    threat_words = [
        "threaten", "kill", "hurt", "attack", "destroy", "rob", "steal",
        "slit", "throat", "stab", "murder", "die", "dead", "weapon",
        "cut", "slash", "gut", "regret", "suffer", "bleed",
    ]
    deal_words = [
        "please", "honour", "honor", "extra", "pay", "deal", "gold",
        "negotiate", "fair", "respect", "worthy", "offer", "double",
        "generous", "kind", "promise", "sworn", "warrior", "champion",
    ]

    is_threat = any(w in last_msg for w in threat_words)
    is_deal   = any(w in last_msg for w in deal_words)

    # ── Hard stops ────────────────────────────────────────────────────
    if is_threat and honor_score < 40:
        return (
            "*Aldric's face drains of colour. He seizes the counter bell and hammers it.* "
            "'GUARDS! Arrest this wretch — NOW!' "
            "Iron-gloved hands seize your shoulders before you can reach the door. "
            "[SYSTEM_ARREST]"
        )

    if is_deal and honor_score >= 40:
        return (
            "*Aldric weighs your words, then slowly extends his hand.* "
            "'A fair argument from a fighter of some standing. Very well — "
            "the blade is yours for 400 gold. Honour has its privileges.' "
            "[SYSTEM_WIN]"
        )

    # ── Varied neutral replies (keyed to turn count to prevent loops) ─
    # Count only user turns so we advance even if Aldric repeats
    user_turn = sum(1 for m in chat_history if m["role"] == "user")

    if honor_score < 40:
        responses = [
            (f"*Aldric crosses his arms.* 'Honour score {honor_score} — "
             "I've seen gutters with more dignity. 600 gold. Final offer.'"),
            ("*Aldric doesn't even look up from his ledger.* "
             "'Still here? The price hasn't changed. 600 gold, dishonourable surcharge.'"),
            ("*Aldric taps the counter twice.* "
             "'Every moment you linger costs you. Pay the 600 or leave my sight.'"),
            ("*Aldric signals his assistant to watch the door.* "
             "'Last warning — 600 gold or I fetch someone to escort you out.'"),
            ("*Aldric's patience snaps.* "
             "'You test me, coward. Pay 600 gold RIGHT NOW or the next words "
             "you hear will be from the city guard.'"),
        ]
    elif honor_score >= 70:
        responses = [
            ("*Aldric smiles broadly.* "
             f"'A champion with honour score {honor_score}! The sword is 500 gold — "
             "but tell me what you have in mind.'"),
            ("*Aldric leans forward with interest.* "
             "'Your reputation opens doors here. Make me an offer — I am listening.'"),
            ("*Aldric polishes the sword case.* "
             "'Few fighters of your calibre pass through. 500 gold, "
             "but I suspect you can do better than a simple purchase.'"),
            ("*Aldric nods thoughtfully.* "
             "'You have proven your worth in the arena. Persuade me and the price drops.'"),
        ]
    else:
        responses = [
            (f"*Aldric gives a measured look.* "
             f"'Honour score {honor_score} — middling. 500 gold. Make your case.'"),
            ("*Aldric drums his fingers.* "
             "'Neither hero nor villain — the boring kind of fighter. "
             "500 gold, no discount without a compelling argument.'"),
            ("*Aldric raises an eyebrow.* "
             "'Still negotiating? Standard price stands at 500. Impress me.'"),
            ("*Aldric sighs.* "
             "'I have other customers. 500 gold — yes or no?'"),
        ]

    # Rotate through responses; clamp to last entry once exhausted
    idx = min(user_turn - 1, len(responses) - 1)
    return responses[max(0, idx)]


def evaluate_rumor(rumor_text: str) -> int:
    """
    Classify a rumor using the Phase-2 ML pipeline.

    Loads
    -----
    models/tfidf_vectorizer.pkl   — fitted TfidfVectorizer (Phase 2)
    models/sentiment_model.pkl    — fitted LogisticRegression (Phase 2)

    Returns
    -------
    int   0 = Dishonorable reputation
          1 = Honorable reputation
    """
    vec_path   = os.path.join(ROOT, "models", "tfidf_vectorizer.pkl")
    model_path = os.path.join(ROOT, "models", "sentiment_model.pkl")

    if not os.path.exists(vec_path) or not os.path.exists(model_path):
        print("[llm_engine] Model files not found — defaulting to Honorable (1).")
        return 1

    try:
        vectorizer = joblib.load(vec_path)
        classifier = joblib.load(model_path)
        features   = vectorizer.transform([rumor_text])
        prediction = int(classifier.predict(features)[0])
        print(f"[llm_engine] evaluate_rumor → class {prediction} "
              f"({'Honorable' if prediction == 1 else 'Dishonorable'})")
        return prediction
    except Exception as e:
        print(f"[llm_engine] evaluate_rumor error: {e}")
        return 1
