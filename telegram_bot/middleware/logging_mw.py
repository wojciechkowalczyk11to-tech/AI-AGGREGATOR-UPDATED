from __future__ import annotations
import logging, json, time
logger = logging.getLogger(__name__)
async def logging_middleware(update, context, next_handler):
    start = time.time()
    logger.info(f"Update {update.update_id} start")
    try:
        res = await next_handler(update, context)
        logger.info(f"Update {update.update_id} end in {time.time()-start:.3f}s")
        return res
    except Exception as e:
        logger.exception(f"Update {update.update_id} failed: {e}")
        raise
