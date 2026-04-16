import os
import json
from dataclasses import dataclass
from groq import Groq


@dataclass
class EvalResult:
    approved: bool
    reason: str
    repair_prompt: str | None = None


def evaluate_response(content_html: str, content_text: str) -> EvalResult:
    # Temporarily disable Groq API eval as requested
    return EvalResult(approved=True, reason="Mock approval (Groq disabled)")

    # api_key = os.environ.get("GROQ_API_KEY")
    # if not api_key or api_key == "replace_me":
    #     print("[!] GROQ_API_KEY missing or invalid. Auto-approving for test.")
    #     return EvalResult(approved=True, reason="Mock approval (no key)")

    client = Groq(api_key=api_key)
    system_prompt = """You are a quality gate for an AI code generator. 
Review the following HTML and text output. 
If it contains a complete, robust web terminal script with PM2 and self-healing logic (no stubs, no "I will do this" without code), approve it.
If it is incomplete, cut off, or missing critical parts, reject it and provide a strict repair_prompt telling the AI to finish or correct the code.
Return ONLY valid JSON in this exact format:
{"approved": true, "reason": "Looks complete"} 
OR 
{"approved": false, "reason": "Missing server.js", "repair_prompt": "You missed the server.js file. Please provide the complete Node.js server code as requested."}"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Text:\n{content_text[:4000]}\n\nHTML:\n{content_html[:4000]}",
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        result = json.loads(completion.choices[0].message.content)
        return EvalResult(
            approved=result.get("approved", False),
            reason=result.get("reason", "No reason provided"),
            repair_prompt=result.get("repair_prompt"),
        )
    except Exception as e:
        print(f"[!] Groq Eval Error: {e}")
        # Fallback to rejecting if API fails, to be safe
        return EvalResult(
            approved=False,
            reason=f"API Error: {str(e)}",
            repair_prompt="Please continue and provide the complete response.",
        )
