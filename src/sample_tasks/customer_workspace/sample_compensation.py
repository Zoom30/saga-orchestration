from loguru import logger


def delete_workspace_record(*args, **kwargs):
    logger.info(f"Called with args: {args}")
    logger.info(f"Called with kwargs: {kwargs}")


def release_claim_subdomain(*args, **kwargs):
    logger.info(f"Called with args: {args}")
    logger.info(f"Called with kwargs: {kwargs}")


def refund(*args, **kwargs):
    logger.info(f"Called with args: {args}")
    logger.info(f"Called with kwargs: {kwargs}")


def deprovision_storage(*args, **kwargs):
    logger.info(f"Called with args: {args}")
    logger.info(f"Called with kwargs: {kwargs}")


class Compensation:
    def __init__(self) -> None:
        self.steps = [
            delete_workspace_record,
            release_claim_subdomain,
            refund,
            deprovision_storage,
        ]
