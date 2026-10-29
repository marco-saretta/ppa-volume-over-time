import contextvars
import logging
import time
from contextlib import contextmanager

log = logging.getLogger(__name__)

# Name of the pipeline stage currently running. "main" outside any stage.
pipeline_stage = contextvars.ContextVar("pipeline_stage", default="main")


def install_stage_field():
    """Add `record.stage` to every log record, so the format can use %(stage)s.

    Applies to all loggers (ours, Hydra's, gurobipy's). Call once at startup.
    """
    old_factory = logging.getLogRecordFactory()

    def factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.stage = f"[{pipeline_stage.get()}]"
        return record

    logging.setLogRecordFactory(factory)


@contextmanager
def stage(name):
    """Label all logs inside the `with` block with `name`, and time the block."""
    token = pipeline_stage.set(name)
    t0 = time.perf_counter()
    log.info("Started")
    try:
        yield
    except Exception:
        log.exception("Failed after %.2fs", time.perf_counter() - t0)
        raise
    else:
        log.info("Finished in %.2fs", time.perf_counter() - t0)
    finally:
        pipeline_stage.reset(token)
