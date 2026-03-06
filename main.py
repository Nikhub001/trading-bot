import asyncio
import logging
import os
from datetime import datetime, timezone, timedelta
from io import BytesIO

from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

from config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_CHANNELS
from signal_parser import parse_signal
from trader import execute_trade

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

client = TelegramClient("trading_bot", TELEGRAM_API_ID, TELEGRAM_API_HASH)

# Track startup time to skip old messages
START_TIME = None


async def get_channel_entities():
    """Resolve channel entities from invite links or usernames."""
    entities = []
    for ch in TELEGRAM_CHANNELS:
        try:
            entity = await client.get_entity(ch)
            entities.append(entity)
            logger.info(f"Listening to channel: {getattr(entity, 'title', ch)}")
        except Exception as e:
            logger.error(f"Could not resolve channel {ch}: {e}")
    return entities


@client.on(events.NewMessage)
async def handler(event):
    global START_TIME

    # Skip messages from before bot started
    msg_time = event.message.date
    if msg_time.tzinfo is None:
        msg_time = msg_time.replace(tzinfo=timezone.utc)
    if START_TIME and msg_time < START_TIME - timedelta(seconds=5):
        return

    # Only process messages from our target channels
    if not event.is_channel and not event.is_group:
        return

    message = event.message
    text = message.text or message.message or ""
    image_bytes = None
    image_mime = "image/jpeg"

    # Download image if present
    if message.media:
        try:
            if isinstance(message.media, MessageMediaPhoto):
                buf = BytesIO()
                await client.download_media(message.media, file=buf)
                image_bytes = buf.getvalue()
                image_mime = "image/jpeg"
                logger.info(f"Photo received from channel, size={len(image_bytes)} bytes")
            elif isinstance(message.media, MessageMediaDocument):
                doc = message.media.document
                if doc and doc.mime_type and doc.mime_type.startswith("image/"):
                    buf = BytesIO()
                    await client.download_media(message.media, file=buf)
                    image_bytes = buf.getvalue()
                    image_mime = doc.mime_type
        except Exception as e:
            logger.warning(f"Could not download media: {e}")

    if not text and not image_bytes:
        return

    preview = (text[:80] + "...") if len(text) > 80 else text
    logger.info(f"New message | text={repr(preview)} | has_image={image_bytes is not None}")

    # Parse signal
    signal = parse_signal(text=text if text else None, image_bytes=image_bytes, image_mime=image_mime)

    if signal:
        logger.info(f"SIGNAL DETECTED: {signal}")
        success = execute_trade(signal)
        if success:
            logger.info("Trade executed successfully!")
        else:
            logger.error("Trade execution failed!")
    else:
        logger.debug("Not a trading signal, skipping")


async def main():
    global START_TIME

    logger.info("Starting trading bot...")
    await client.start()
    logger.info("Telegram client connected")

    START_TIME = datetime.now(timezone.utc)

    channels = await get_channel_entities()
    logger.info(f"Bot started, listening to {len(channels)} channels")

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
