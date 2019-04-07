import itertools

import psycopg2
import psycopg2.extras
import sys
import requests
from bs4 import BeautifulSoup
import time
import datetime
from utils.logger import setup_logger
from requests.exceptions import ConnectionError

import copy
import re
import pandas as pd
import os
from urllib3.exceptions import ReadTimeoutError, ConnectTimeoutError

__all__ = 'CCASS'
logger = setup_logger(__all__)

def main():
    logger.info("Testing")


if __name__ == "__main__":
    main()
