
import os
import json
import time
import logging
_logger = logging.getLogger(__name__)

class Fal:
    def __init__(self, api_key=None):
        self.api_key=api_key