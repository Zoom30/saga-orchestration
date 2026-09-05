from loguru import logger


def release_flight_seats(*args, **kwargs):
    logger.info(f"Called with args: {args}")
    logger.info(f"Called with kwargs: {kwargs}")


def release_hotel_room(*args, **kwargs):
    logger.info(f"Called with args: {args}")
    logger.info(f"Called with kwargs: {kwargs}")


def refund(*args, **kwargs):
    logger.info(f"Called with args: {args}")
    logger.info(f"Called with kwargs: {kwargs}")


class Compensation:
    def __init__(self):
        self.steps = [release_flight_seats, release_hotel_room, refund]
