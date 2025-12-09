import os
import time
import pandas as pd
from entsoe import EntsoePandasClient
from entsoe.exceptions import NoMatchingDataError
from dotenv import load_dotenv

# 1. Setup Environment
load_dotenv()  # Load API key from .env file
API_KEY = os.getenv("ENTSOE_API_KEY")
client = EntsoePandasClient(api_key=API_KEY)

start = pd.Timestamp('20240101', tz='Europe/Brussels')
end = pd.Timestamp('20250101', tz='Europe/Brussels')
country_code = 'AT'  # Austria

data = client.query_generation(country_code, start=start, end=end, psr_type=None)

data.to_csv("./data/01_raw/data1year.csv")

print(data.head(24))
