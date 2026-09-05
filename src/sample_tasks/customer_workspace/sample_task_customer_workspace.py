from loguru import logger


def create_workspace_record(*args, **kwargs):
    logger.info(f"Called with args: {args}")
    logger.info(f"Called with kwargs: {kwargs}")


def claim_subdomain(*args, **kwargs):
    logger.info(f"Called with args: {args}")
    logger.info(f"Called with kwargs: {kwargs}")


def charge_bill(*args, **kwargs):
    logger.info(f"Called with args: {args}")
    logger.info(f"Called with kwargs: {kwargs}")


def provision_storage(*args, **kwargs):
    logger.info(f"Called with args: {args}")
    logger.info(f"Called with kwargs: {kwargs}")


def send_welcome_email(*args, **kwargs):
    logger.info(f"Called with args: {args}")
    logger.info(f"Called with kwargs: {kwargs}")


class CustomerWorkspace:
    def __init__(self) -> None:
        self.steps = [
            create_workspace_record,
            claim_subdomain,
            charge_bill,
            provision_storage,
            send_welcome_email,
        ]
