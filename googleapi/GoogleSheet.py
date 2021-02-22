from googleapiclient import discovery
import json
from config import config
from datetime import datetime


def filter(data):
    filtered={}
    fields = ["seq", "date", "week", "title", "tags", "certainty_num", "certainty", "impact", "url"]
    for f in fields:
        if f == "date":
            filtered[f] = datetime.fromtimestamp(data[f]/1000).date().isoformat()
        elif f == "certainty_num":
            try:
                filtered[f] = int(data[f])
            except:
                filtered[f] = 100
        else:
            filtered[f] = data[f]

    return filtered

def insert_to_google_sheet(data, credentials):
    values = []
    news = json.loads(data)

    service = discovery.build('sheets', 'v4', credentials=credentials)

    value_input_option = 'RAW'
    insert_data_option = 'INSERT_ROWS'

    # get number of rows

    request = service.spreadsheets().values().get(spreadsheetId=config.SPREADSHEET_ID, range=config.RANGE)

    seq_list = request.execute()['values']
    insert_index = len(seq_list)-1
    last_seq_num = int(seq_list[-1][0])
    print(last_seq_num)

    for i, d in enumerate(news):
        if "label" not in d:
            d["label"] = False
        if d["label"]:
            d["seq"] = (last_seq_num+i+1)
            values.append(list(filter(d).values()))

    range_ = 'Main_Log!A{}:I{}'.format(insert_index, insert_index)
    print(range_)

    value_range_body = {
        "range": range_,
        "majorDimension": "ROWS",
        "values": values
    }

    request = service.spreadsheets().values().append(spreadsheetId=config.SPREADSHEET_ID, range=range_,
                                                     valueInputOption=value_input_option,
                                                     insertDataOption=insert_data_option, body=value_range_body)
    response = request.execute()
    return response
