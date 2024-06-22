import pandas as pd
import datetime
import scrape_data
import upload_data

date_1 = datetime.date.today() - datetime.timedelta(days=1)
date_2 = datetime.date.today() - datetime.timedelta(days=1)

print(f'script started. pulling data from {date_1} to {date_2}')

date_list = pd.date_range(start=date_1,end=date_2).to_list()

for date in date_list:
    data = scrape_data.get_all_data_on_date(date)
    upload_data.upload_all_data_on_date(data, date)

print("script ended")
