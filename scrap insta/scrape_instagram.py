import requests
from bs4 import BeautifulSoup
import re
import concurrent.futures

def find_instagram_links(url):
    try:
        response = requests.get(url, timeout=5)  # Wait for a maximum of 5 seconds
        response.raise_for_status()  # Raise an error for bad status codes
        soup = BeautifulSoup(response.text, 'html.parser')
        links = set()  # Using a set to avoid duplicate links

        # Regex pattern to match Instagram links
        instagram_url_pattern = re.compile(r'https?://(www\.)?instagram\.com/[\w.]+')
        # break if a single instagram link is found
        for link in soup.find_all('a', href=True):
            href = link['href']
            if instagram_url_pattern.match(href) and href not in links:
                links.add(href)

        if not links:
            return set()

        return list(links)
    except (requests.RequestException, requests.Timeout) as e:
        return set()


def get_username(url):
    # FORMAT: https://www.instagram.com/<username>/
    return url.split('/')[3]


# list out current CSV files in the directory in the form of 
# [1] file1.csv
# [2] file2.csv 
# based on that, chose the file from user input
# then extract the URLs from the file and store them in a list
# then loop through the list and call the function find_instagram_links(url) for each URL
# add the instagram links,as well as username (gotten from the link using get_username function) and add them to the file
def add_instagram_links_to_csv():
    i = 0
    print("Pick a file to extract instagram links to: ")
    # list out current CSV files in the directory
    import os
    files = os.listdir()
    csv_files = []
    for file in files:
        if file.endswith('.csv'):
            csv_files.append(file)
    for index, file in enumerate(csv_files):
        print(f'[{index + 1}] {file}')
    # based on that, chose the file from user input
    file_index = int(input('Enter the file number: '))
    file = csv_files[file_index - 1]
    # then extract the URLs from the CSV file using pandas and store them in a list
    import pandas as pd
    df = pd.read_csv(file)
    urls = df['Domain name'].tolist()

    # Add HTTPS://www. to the URLs that don't have it
    for index, url in enumerate(urls):
        if not url.startswith('http'):
            urls[index] = 'https://www.' + url

    # then loop through the list and call the function find_instagram_links(url) for each URL
    instagram_links = []
    usernames = []
   
    with concurrent.futures.ThreadPoolExecutor(max_workers=300) as executor:
        future_to_url = {executor.submit(find_instagram_links, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                links = future.result()
                i += 1
                if links:
                    for link in links: 
                        instagram_links.append(link)
                        usernames.append(get_username(link))
                    # Neatly print in the order [<attempt number>] <Instagram links found>
                    print(f'[{i}] {len(links)} Instagram links found for {url}')
                else:
                    print(f'Found 0 links for {url}')
            except Exception as e:
                print(f'An error occurred while processing {url}: {e}')
    # print number of links found
    print(f'Found {len(instagram_links)} links')
   
    df = pd.DataFrame()

    df['Username'] = usernames
   
    list_df = pd.read_csv('../infos/list.csv')
    # compare the "Username" column of the list_df with the "Username" column of the df, appending at the end of the list_df if the username is not already in the list_df
    for username in usernames:
        if username not in list_df['Username'].tolist():
            list_df = list_df.append(df[df['Username'] == username], ignore_index=True)
    # save the list_df to the list.csv file
    list_df.to_csv('../infos/list.csv', index=False)

    print(f'Added Instagram links to ../infos/list.csv')

    
    

if __name__ == '__main__':
    add_instagram_links_to_csv()