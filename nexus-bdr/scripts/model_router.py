#!/usr/bin/env python3
"""
OpenRouter Model Router — Nexus BDR Agent
==========================================
Intelligent model routing that cuts API costs 10-50x.

Routes research/gathering calls → cheap models (Llama 3.1 70B, Mixtral)
Routes synthesis/strategy calls → Claude Sonnet
Routes simple extraction calls → Llama 3.1 8B (near-free)

Setup:
    export OPENROUTER_API_KEY="sk-or-..."
    export ANTHROPIC_API_KEY="sk-ant-..."  (fallback + premium calls)

Pricing comparison (per 1M tokens input):
    Claude Sonnet 4.5:  $3.00
    Llama 3.1 70B:      $0.18  (17x cheaper)
    Llama 3.1 8B:       $0.06  (50x cheaper)
    Mixtral 8x22B:      $0.20  (15x cheaper)
    DeepSeek V3:        $0.14  (21x cheaper)

Brief cost comparison:
    All-Claude:    ~$1.00-1.50 per brief
    With router:   ~$0.10-0.20 per brief
"""

import os, json, time, re
from datetime import datetime

try:
    import requests
except ImportError:
    print("pip install requests"); exit(1)

# ── CONFIG ──

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

# Model tiers
MODELS = {
    # Tier 1: Near-free. Simple extraction, parsing, classification.
    "cheap": {
        "provider": "openrouter",
        "model": "meta-llama/llama-3.1-8b-instruct",
        "max_tokens": 4096,
        "cost_per_1m_in": 0.06,
        "label": "Llama 8B",
    },
    # Tier 2: Good quality. Research gathering, product analysis, people finding.
    "research": {
        "provider": "openrouter",
        "model": "meta-llama/llama-3.1-70b-instruct",
        "max_tokens": 8192,
        "cost_per_1m_in": 0.18,
        "label": "Llama 70B",
    },
    # Tier 2 alt: Strong reasoning at low cost.
    "reasoning": {
        "provider": "openrouter",
        "model": "deepseek/deepseek-chat-v3-0324",
        "max_tokens": 8192,
        "cost_per_1m_in": 0.14,
        "label": "DeepSeek V3",
    },
    # Tier 3: Premium. Strategy synthesis, outreach copy, financial modeling.
    "premium": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-5-20250929",
        "max_tokens": 8192,
        "cost_per_1m_in": 3.00,
        "label": "Claude Sonnet",
    },
    # Tier 3 alt: Premium via OpenRouter (if Anthropic rate limited).
    "premium_or": {
        "provider": "openrouter",
        "model": "anthropic/claude-sonnet-4-5-20250929",
        "max_tokens": 8192,
        "cost_per_1m_in": 3.00,
        "label": "Claude via OR",
    },
}

# Which tier to use for each brief phase
PHASE_ROUTING = {
    "phase_1_recon": "research",          # Company research — good model, many searches
    "phase_2_products": "research",        # Product analysis — needs comprehension
    "phase_3_people": "research",          # People finding — pattern matching
    "phase_4_competitive": "reasoning",    # Competitive intel — needs analytical depth
    "phase_5_financial": "premium",        # Financial modeling — needs precision
    "phase_6_synthesis": "premium",        # Strategy + outreach — needs quality writing
    "enrichment": "cheap",                 # Lead enrichment — simple extraction
    "scoring": "cheap",                    # Lead scoring — classification
    "social_scan": "research",             # Social monitoring — comprehension
    "social_analysis": "reasoning",        # Social analysis — analytical
    "trigger_detection": "cheap",          # Signal detection — pattern matching
    "email_draft": "premium",             # Outreach copy — needs quality
    "heygen_script": "premium",           # Video scripts — needs quality
    "default": "research",                 # Fallback
}

# ── TRACKING ──

class CostTracker:
    def __init__(self):
        self.calls = []
        self.session_start = datetime.utcnow().isoformat()

    def log(self, tier, model, input_tokens, output_tokens, cost_est, duration, success):
        self.calls.append({
            "time": datetime.utcnow().isoformat(),
            "tier": tier,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_est": cost_est,
            "duration_s": round(duration, 1),
            "success": success,
        })

    def summary(self):
        if not self.calls:
            return "No API calls made."
        total_cost = sum(c["cost_est"] for c in self.calls)
        total_input = sum(c["input_tokens"] for c in self.calls)
        total_output = sum(c["output_tokens"] for c in self.calls)
        by_tier = {}
        for c in self.calls:
            t = c["tier"]
            if t not in by_tier:
                by_tier[t] = {"calls": 0, "cost": 0, "tokens": 0}
            by_tier[t]["calls"] += 1
            by_tier[t]["cost"] += c["cost_est"]
            by_tier[t]["tokens"] += c["input_tokens"] + c["output_tokens"]

        lines = [f"\n  ═══ Cost Summary ═══",
                 f"  Total: ${total_cost:.4f} | {len(self.calls)} calls | {total_input+total_output:,} tokens"]
        # What it would have cost all-Claude
        claude_cost = (total_input * 3.00 + total_output * 15.00) / 1_000_000
        if claude_cost > 0:
            savings = max(0, (1 - total_cost / claude_cost) * 100)
            lines.append(f"  All-Claude would cost: ${claude_cost:.4f} | Savings: {savings:.0f}%")
        for t, d in sorted(by_tier.items()):
            lines.append(f"    {t}: {d['calls']} calls, ${d['cost']:.4f}, {d['tokens']:,} tokens")
        return "\n".join(lines)

    def save(self, path):
        with open(path, "w") as f:
            json.dump({"session": self.session_start, "calls": self.calls, "summary": self.summary()}, f, indent=2)


tracker = CostTracker()


# ── API CALLS ──

def call_openrouter(model_id, system_prompt, user_prompt, max_tokens=4096, temperature=0.3, tools=None):
    """Call OpenRouter API."""
    if not OPENROUTER_KEY:
        raise ValueError("OPENROUTER_API_KEY not set")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    payload = {
        "model": model_id,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    # OpenRouter supports some models with web search via plugins
    if tools:
        payload["tools"] = tools

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": "https://nexus-bdr.local",
        "X-Title": "Nexus BDR Agent",
    }

    resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)

    if resp.status_code == 429:
        raise Exception("Rate limited")
    if resp.status_code != 200:
        raise Exception(f"OpenRouter {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    choice = data.get("choices", [{}])[0]
    text = choice.get("message", {}).get("content", "")
    usage = data.get("usage", {})

    return text, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def call_anthropic(system_prompt, user_prompt, max_tokens=4096, tools=None):
    """Call Anthropic API directly."""
    if not ANTHROPIC_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set")

    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
    }

    payload = {
        "model": "claude-sonnet-4-5-20250929",
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }

    if tools:
        payload["tools"] = tools

    resp = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=300)

    if resp.status_code == 429:
        raise Exception("Rate limited")
    if resp.status_code != 200:
        raise Exception(f"Anthropic {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    text = "\n".join(b["text"] for b in data.get("content", []) if b.get("type") == "text")
    usage = data.get("usage", {})

    return text, usage.get("input_tokens", 0), usage.get("output_tokens", 0)


# ── ROUTER ──

def routed_call(phase, system_prompt, user_prompt, max_tokens=None, tools=None, retries=2):
    """
    Route an API call to the appropriate model based on phase.

    Args:
        phase: Key from PHASE_ROUTING (e.g., "phase_1_recon", "enrichment")
        system_prompt: System/instruction prompt
        user_prompt: User prompt with the actual task
        max_tokens: Override max tokens (uses model default if None)
        tools: List of tool definitions (e.g., web_search)
        retries: Number of retry attempts

    Returns:
        str: Model response text
    """
    tier = PHASE_ROUTING.get(phase, PHASE_ROUTING["default"])
    model_config = MODELS[tier]
    mt = max_tokens or model_config["max_tokens"]

    # If tools include web_search and we're using OpenRouter, fall back to Anthropic
    # (web_search is Anthropic-native)
    has_web_search = tools and any(
        (isinstance(t, dict) and t.get("type", "").startswith("web_search")) or
        (isinstance(t, dict) and t.get("name") == "web_search")
        for t in tools
    )

    if has_web_search and model_config["provider"] == "openrouter":
        # Web search requires Anthropic API — upgrade to premium
        tier = "premium"
        model_config = MODELS[tier]
        # Format tools for Anthropic
        tools = [{"type": "web_search_20250305", "name": "web_search"}]

    for attempt in range(retries + 1):
        start = time.time()
        try:
            if model_config["provider"] == "anthropic":
                text, in_tok, out_tok = call_anthropic(system_prompt, user_prompt, mt, tools)
            else:
                text, in_tok, out_tok = call_openrouter(model_config["model"], system_prompt, user_prompt, mt, tools=tools)

            duration = time.time() - start
            # Use actual output pricing: Anthropic=$15/1M out, others ~4x input
            out_rate = 15.0 if model_config["provider"] == "anthropic" else model_config["cost_per_1m_in"] * 4
            cost = (in_tok * model_config["cost_per_1m_in"] + out_tok * out_rate) / 1_000_000
            tracker.log(tier, model_config["model"], in_tok, out_tok, cost, duration, True)

            print(f"    ✓ {model_config['label']} | {in_tok+out_tok:,} tok | ${cost:.4f} | {duration:.0f}s")
            return text

        except Exception as e:
            duration = time.time() - start
            tracker.log(tier, model_config["model"], 0, 0, 0, duration, False)

            if "Rate limited" in str(e) and attempt < retries:
                wait = 15 * (attempt + 1)
                print(f"    ⏳ {model_config['label']} rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue

            # Try fallback: if OpenRouter failed, try Anthropic; if Anthropic failed, try OpenRouter
            if attempt == retries and model_config["provider"] == "openrouter" and ANTHROPIC_KEY:
                print(f"    ↪ Falling back to Anthropic...")
                try:
                    text, in_tok, out_tok = call_anthropic(system_prompt, user_prompt, mt, tools)
                    cost = (in_tok * 3.0 + out_tok * 15.0) / 1_000_000
                    tracker.log("premium_fallback", "claude-sonnet", in_tok, out_tok, cost, time.time()-start, True)
                    return text
                except:
                    pass

            if attempt == retries and model_config["provider"] == "anthropic" and OPENROUTER_KEY:
                print(f"    ↪ Falling back to OpenRouter Claude...")
                try:
                    text, in_tok, out_tok = call_openrouter("anthropic/claude-sonnet-4-5-20250929", system_prompt, user_prompt, mt)
                    cost = (in_tok * 3.0 + out_tok * 15.0) / 1_000_000
                    tracker.log("premium_or_fallback", "claude-via-or", in_tok, out_tok, cost, time.time()-start, True)
                    return text
                except:
                    pass

            print(f"    ❌ {model_config['label']}: {str(e)[:150]}")
            print(f"    ❌ All retries and fallbacks exhausted for tier '{tier}'")
            return ""

    print(f"    ❌ Route failed: no response after {retries+1} attempts")
    return ""


def parse_json_response(text):
    """Extract JSON from model response."""
    if not text:
        return None
    # Try ```json blocks first
    m = re.search(r'```json\s*\n?(.*?)\n?```', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except:
            pass
    # Try raw JSON
    depth = 0
    start = None
    for i, c in enumerate(text):
        if c == '{':
            if depth == 0: start = i
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    return json.loads(text[start:i+1])
                except:
                    start = None
    return None


# ── CONVENIENCE ──

def check_available_providers():
    """Check which API providers are configured."""
    providers = {}
    if OPENROUTER_KEY:
        providers["openrouter"] = True
        print(f"  ✅ OpenRouter configured")
    else:
        providers["openrouter"] = False
        print(f"  ❌ OpenRouter: set OPENROUTER_API_KEY")

    if ANTHROPIC_KEY:
        providers["anthropic"] = True
        print(f"  ✅ Anthropic configured")
    else:
        providers["anthropic"] = False
        print(f"  ❌ Anthropic: set ANTHROPIC_API_KEY")

    if not any(providers.values()):
        print(f"\n  ⚠️  No API providers configured. Set at least one API key.")
        return False
    return True


def estimate_brief_cost(use_openrouter=True):
    """Estimate cost of running a full 6-phase brief."""
    if use_openrouter:
        # Phases 1-4 on cheap/research models, 5-6 on Claude
        # ~3000 input tokens per phase, ~2000 output
        cheap_phases = 4  # phases 1-4
        premium_phases = 2  # phases 5-6
        cheap_cost = cheap_phases * (3000 * 0.18 + 2000 * 0.72) / 1_000_000
        premium_cost = premium_phases * (3000 * 3.0 + 2000 * 15.0) / 1_000_000
        return cheap_cost + premium_cost
    else:
        # All Claude
        return 6 * (3000 * 3.0 + 2000 * 15.0) / 1_000_000


if __name__ == "__main__":
    print("\n  ═══ Nexus Model Router ═══")
    check_available_providers()
    or_cost = estimate_brief_cost(True)
    claude_cost = estimate_brief_cost(False)
    print(f"\n  Brief cost with OpenRouter:  ${or_cost:.3f}")
    print(f"  Brief cost all-Claude:       ${claude_cost:.3f}")
    print(f"  Savings:                     {(1-or_cost/claude_cost)*100:.0f}%")
    print()
