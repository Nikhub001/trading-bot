import json
import logging
import google.generativeai as genai
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

PROMPT = """You are a crypto trading signal analyzer. Analyze this message from a Telegram trading channel.

Determine if this is an actionable ENTRY trading signal.

NOT a signal (return null): trade results/PnL screenshots, market analysis without clear entry point, general news, memes, motivation posts, congratulations, discussions.

IS a signal: clear instruction to open a trade with a specific crypto pair, direction (long/short/buy/sell), and ideally an entry price.

If it IS a signal, return ONLY valid JSON (no markdown, no explanation):
{
  "is_signal": true,
  "symbol": "BTCUSDT",
  "direction": "long",
  "entry": 95000,
  "stop_loss": 93000,
  "take_profit": [98000, 100000],
  "confidence": 0.9
}

Rules:
- symbol: always format as COINUSDT (e.g. BTCUSDT, ETHUSDT)
- direction: "long" or "short" only
- entry: price number or null for market order
- stop_loss: price or null
- take_profit: array of prices or null
- confidence: 0.0-1.0

If NOT a signal, return ONLY: {"is_signal": false}"""


def parse_signal(text=None, image_bytes=None, image_mime="image/jpeg"):
    try:
        parts = [PROMPT]

        if text:
            parts.append(f"\nMessage text:\n{text}")

        if image_bytes:
            parts.append({
                "mime_type": image_mime,
                "data": image_bytes
            })

        if not text and not image_bytes:
            return None

        response = model.generate_content(parts)
        raw = response.text.strip()

        # Strip markdown code blocks if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)

        if not data.get("is_signal"):
            return None

        confidence = data.get("confidence", 0)
        if confidence < 0.7:
            logger.info(f"Signal detected but low confidence ({confidence}), skipping")
            return None

        logger.info(f"Signal parsed: {data}")
        return data

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse Gemini response as JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Signal parsing error: {e}")
        return None
