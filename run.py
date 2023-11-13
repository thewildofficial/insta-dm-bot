import json
import os
import pandas as pd
from src.instadm import InstaDM
import datetime
import concurrent.futures

start_time = datetime.datetime.now()

with open('infos/accounts.json') as f:
    accounts = json.load(f)

csv_files = [file for file in os.listdir('infos') if file.endswith('.csv')]

for index, file in enumerate(csv_files):
    print(f'[{index + 1}] {file}')

file_index = int(input('Enter the file number: '))
file = csv_files[file_index - 1]

df = pd.read_csv(f'infos/{file}')
df['Reached?'] = df['Reached?'].astype(str)
used_usernames = df.loc[df['Reached?'] == 'Yes', 'Username']

df = df[~df['Username'].isin(used_usernames)]
usernames = df['Username'].tolist()

with open('infos/messages.txt', 'r') as f:
    messages = f.read().splitlines()

counter = 0

def send_messages(account):
    global counter
    insta = InstaDM(username=account["username"], password=account["password"], headless=False)
    for i in range(30):
        if not usernames:
            break
        username = usernames.pop()
        insta.sendMessage(user=username, message=messages,file=file)
        df = pd.read_csv('infos/' + file)
        df.loc[df['Username'] == username, 'Assigned'] = account["username"]
        df.to_csv('infos/' + file, index=False)
        counter += 1
        # print: [time] username -> account: Message [counter]
        print(f'[{datetime.datetime.now()}] {account["username"]} -> {username}: Local: [{i+1}] : Global: [{counter}]')
    insta.teardown()

with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(send_messages, accounts)

print("=====================================")
print("FINISHED")
# print total time taken in seconds, total number of messages
end_time = datetime.datetime.now()
print(f'Total time taken: {end_time - start_time}')
print(f'Total messages sent: {counter}')

print("=====================================")
