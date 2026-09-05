from loguru import logger


def reserve_flight_seats(*args, **kwargs):
    logger.info(f"Called with args: {args}")
    logger.info(f"Called with kwargs: {kwargs}")


def reserve_hotel_room(*args, **kwargs):
    logger.info(f"Called with args: {args}")
    logger.info(f"Called with kwargs: {kwargs}")


def process_payment(*args, **kwargs):
    logger.info(f"Called with args: {args}")
    logger.info(f"Called with kwargs: {kwargs}")


def notify(*args, **kwargs):
    logger.info(f"Called with args: {args}")
    logger.info(f"Called with kwargs: {kwargs}")


class BookTrip:
    def __init__(self):
        self.steps = [reserve_flight_seats, reserve_hotel_room, process_payment, notify]
