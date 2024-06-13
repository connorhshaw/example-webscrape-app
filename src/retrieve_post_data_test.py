import pandas as pd
import datetime
import scrape_data
import upload_data

print("script started")

date_1 = datetime.date(2024, 1, 1)
date_2 = datetime.date(2024, 1, 1)

date_list = pd.date_range(start=date_1,end=date_2).to_list()

for date in date_list:
    data = scrape_data.get_all_data_on_date(date)
    upload_data.upload_all_data_on_date(data, date)

print("script ended")
