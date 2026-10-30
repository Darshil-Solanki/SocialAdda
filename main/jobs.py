import logging

logger = logging.getLogger(__name__)


def enqueue(task, *args):
    """Queues a background task after the database write that needs it.

    A broker outage is logged rather than raised: the write already succeeded, and the user should not see
    a failure for a side effect such as a welcome email or a feed update.
    """
    try:
        task.delay(*args)
    except Exception:
        logger.exception('Could not queue background task %s', task.name)
        return False
    return True
