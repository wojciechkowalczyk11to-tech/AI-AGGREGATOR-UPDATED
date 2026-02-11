from __future__ import annotations
import asyncio
from telegram.constants import ChatAction
async def _send_typing_periodic(update, interval=4.0):
    try:
        while True:
            await update.effective_chat.send_action(ChatAction.TYPING)
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        import logging
        logging.getLogger(__name__).debug("Typing periodic task cancelled")
class TypingIndicator:
    def __init__(self, update, context): self.update, self.context, self._task = update, context, None
    async def __aenter__(self):
        if self.update.effective_chat: self._task = asyncio.create_task(_send_typing_periodic(self.update))
        return self
    async def __aexit__(self, et, ev, tb):
        if self._task:
            self._task.cancel()
            try: await self._task
            except asyncio.CancelledError:
                import logging
                logging.getLogger(__name__).debug("Typing indicator task awaited and confirmed cancelled")
