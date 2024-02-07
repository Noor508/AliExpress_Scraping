import requests
import json
import bs4
import pandas as pd
from sqlalchemy import create_engine

def scrape_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        html = response.text
        soup = bs4.BeautifulSoup(html, "html.parser")
        scripts = soup.find_all("script")

        inner_html = str(scripts[2].string)
        inner_html = inner_html.replace('window._dida_config_ = {"pageVersion":"ff8ad60b0a0d1fbfc9e484ea303a7f44","pageName":"search-pc"};', "")
        inner_html = inner_html.replace('window._dida_config_._init_data_= ', "")
        inner_html = inner_html.replace("data", '"data"', 1)

        json_data = json.loads(inner_html)

        # Create a list to store data
        data_list = []

        for item in json_data["data"]["data"]["root"]["fields"]["mods"]["itemList"]["content"]:
            prod_Id = item['productId']
            title = item["title"]["displayTitle"]
            price = item['prices']['salePrice']['formattedPrice']    
            img_url = item['image']['imgUrl']
            
            rating = item['evaluation']['starRating'] if 'evaluation' in item else None

            url = f"www.aliexpress.com/item/{prod_Id}.html"

            data_list.append({
                "ProductId": prod_Id,
                "Title": title,
                "Price": price,
                "ImageUrl": img_url,
                "Rating": rating,
                "ProductUrl": url
            })

        return data_list
    except Exception as e:
        print(f"An error occurred while scraping page {url}: {e}")
        return []


def scrape_multiple_pages(base_url, num_pages):
    all_data = []

    for page in range(1, num_pages + 1):
        url = f"{base_url}&page={page}"
        page_data = scrape_page(url)
        all_data.extend(page_data)

    return all_data

try:
    # Input parameters
    userSearch = input("Enter Your desired product::")
    Search = userSearch.replace(" ", "-")
    base_url = f"https://www.aliexpress.com/w/wholesale-{userSearch}.html?g=y&SearchText={Search}"

    # Number of pages to scrape
    num_pages = int(input("Enter the number of pages to scrape: "))

    # Scraping data from multiple pages
    data_list = scrape_multiple_pages(base_url, num_pages)

    # Create a DataFrame
    df = pd.DataFrame(data_list)
    print(df)

    # Database configuration
    db_user = "root"
    db_password = "root"
    db_host = "localhost"
    db_port = "3306"
    db_name = "aliexpress"

    # Create a MySQL connection
    engine = create_engine(f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")

    # Store DataFrame in MySQL database
    table_name = "products"
    df.to_sql(name=table_name, con=engine, if_exists='append', index=False)

    # Close the database connection
    engine.dispose()

    print(f"DataFrame has been stored in the '{table_name}' table of the '{db_name}' schema.")
except Exception as e:
    print(f"An error occurred: {e}")
