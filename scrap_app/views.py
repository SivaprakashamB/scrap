from django.shortcuts import render

# Create your views here.
import requests
import datetime
from django.http import HttpResponse
import time
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
import urllib.parse
from selenium.webdriver.common.by import By

# from datetime import datetime
from django.http import HttpResponse


def index(request):
    now = datetime.now()
    html = f'''
    <html>
        <body>
            <h1>Hello from PUPI!</h1>
            <p>The current time is { now }.</p>
        </body>
    </html>
    '''
    return HttpResponse(html)


def decide_fun(request):
    slug = request.GET['slug']
    if 'zomato' in slug:
        return zomato_scrap(request)
    elif 'swiggy' in slug:
        return swiggy_scrape(request)
    elif not slug:
        return HttpResponse("Kindly Give API Value in Slug ")
    else:
        slug = request.GET['slug']
        return scrape_and_return_csv(request, slug)


def scrape_and_return_csv(request, slug):

    url = f'https://cw-api.takeaway.com/api/v33/restaurant?slug={slug}'
    slug = slug
    headers = {
        'authority': 'cw-api.takeaway.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en',
        'origin': 'https://www.just-eat.fr',
        'referer': 'https://www.just-eat.fr/',
        'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': 'Linux',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'x-country-code': 'fr',
        'x-datadog-origin': 'rum',
        'x-datadog-parent-id': '8119252046239753939',
        'x-datadog-sampling-priority': '1',
        'x-datadog-trace-id': '1339555150929921155',
        'x-language-code': 'en',
        'x-requested-with': 'XMLHttpRequest',
        'x-session-id': '7d991a28-8f0e-4ab9-bb3b-b98bf9f4f0a2',
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        csv_file_path = f'{slug}{timestamp}.csv'

        # Create the csv file and write data's in row by row and export.
        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)

            csv_writer.writerow(['Item Name', 'Item Description', 'Item Type', 'Item Image URL'])

            brand_name = data['brand']['name']
            menu_categories = data['menu']['categories']

            for category in menu_categories:
                category_name = category['name']
                products = category['productIds']

                for product_id in products:
                    # Get the item details using the product_id
                    item = data['menu']['products'][product_id]
                    item_name = item['name']
                    item_description = ', '.join(item['description'])
                    item_type = category_name
                    item_image_url = item['imageUrl']

                    csv_writer.writerow([item_name, item_description, item_type, item_image_url])

        with open(csv_file_path, 'rb') as csv_file:
            response = HttpResponse(csv_file.read(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{csv_file_path}"'

        return response

    else:
        return HttpResponse('Failed to fetch the webpage.')


def zomato_scrap(request):
    slug = request.GET['slug']
    api_url = urllib.parse.unquote(slug)
    # api_url = "https://www.zomato.com/webroutes/getPage?page_url=/madurai/suganya-parotta-kadai-balarengapuram/order?contextual_menu_params=eyJkaXNoX3NlYXJjaCI6eyJ0aXRsZSI6IkJlc3QgaW4gQ2hpY2tlbiIsImRpc2hfaWRzIjpbIjU1MjgwIl0sImN1aXNpbmVfaWRzIjpbXX19&location=&isMobile=0"
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        try:
            data = response.json()
        except requests.RequestException as e:
            return HttpResponse(f'Error fetching the URL: {str(e)}')

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        csv_file_path = f'zomato_csv_{timestamp}.csv'

        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)

            csv_writer.writerow(['Item Name', 'Item Description', 'Item Type', 'Item Image URL'])

            for menu in data['page_data']['order']['menuList']['menus']:
                for category in menu['menu']['categories']:
                    for item_data in category['category']['items']:
                        item_name = item_data['item']['name']
                        item_image_url = item_data['item'].get('item_image_url', '')
                        item_price = item_data['item']['price']
                        item_description = item_data['item']['desc']
                        item_type = item_data['item']['item_type']

                        csv_writer.writerow([item_name, item_description, item_type, item_image_url])

        with open(csv_file_path, 'rb') as csv_file:
            response = HttpResponse(csv_file.read(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{csv_file_path}"'
        return response

    else:
        return HttpResponse('Failed to fetch the webpage.')


def swiggy_scrape(request):


    slug = request.GET['slug']
    url = urllib.parse.unquote(slug)
    # url = "https://www.swiggy.com/restaurants/jayaram-bakery-restaurant-near-kalavasal-signal-ss-colony-madurai-80294"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(options=options)

        driver.get(url)

        # Scroll down repeatedly until no new images load
        prev_image_count = 0
        image_count = 0
        while True:
            driver.execute_script("window.scrollBy(0, window.innerHeight);")
            time.sleep(2)
            image_elements = driver.find_elements(By.CSS_SELECTOR, 'img.styles_itemImage__3CsDL')
            current_image_count = len(image_elements)
            if current_image_count == prev_image_count:
                break
            prev_image_count = current_image_count

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        item_names = []
        item_prices = []
        item_descriptions = []
        image_urls = []
        food_types = []
        restaurant_name = ""
        restaurant_cuisines = ""
        customisable_names = []
        customisable_prices = []

        restaurant_name_element = soup.find('p', class_='RestaurantNameAddress_name__2IaTv')
        restaurant_cuisines_element = soup.find('p', class_='RestaurantNameAddress_cuisines__mBHr2')
        if restaurant_name_element:
            restaurant_name = restaurant_name_element.text.strip()
        if restaurant_cuisines_element:
            restaurant_cuisines = restaurant_cuisines_element.text.strip()

        item_elements = soup.find_all('div', class_='styles_item__3_NEA')

        for item_element in item_elements:
            item_name_element = item_element.find('h3', class_='styles_itemNameText__3ZmZZ')
            item_name = item_name_element.text.strip() if item_name_element else "N/A"

            price_element = item_element.find_next('span', class_='rupee')
            item_price = price_element.text.strip() if price_element else "N/A"

            description_element = item_element.find_previous('p', class_='ScreenReaderOnly_screenReaderOnly___ww-V')
            item_description = description_element.text.strip() if description_element else "N/A"

            img_element = item_element.find('img', class_='styles_itemImage__3CsDL')
            img_url = img_element.get('src') if img_element else 'N/A'

            food_type_element = item_element.find('i', class_='icon-Veg')
            if food_type_element:
                food_type = 'Veg'
            else:
                food_type_element = item_element.find('i',
                                                      class_='icon-NonVeg')
                if food_type_element:
                    food_type = 'Non-Veg'
                else:
                    food_type = 'N/A'

            food_type_value = 1 if food_type == 'Veg' else (2 if food_type == 'Non-Veg' else 0)

            item_names.append(item_name)
            item_prices.append(item_price)
            item_descriptions.append(item_description)
            image_urls.append(img_url)
            food_types.append(food_type_value)

            customisable_button = item_element.find('div', class_='_1C1Fl')  # _1C1Fl
            if customisable_button:
                customisable_names.append('Customisable')
                customisable_prices.append('N/A')

                add_button = item_element.find('div', class_='_1RPOp')
                if add_button:
                    try:
                        add_button.click()
                        time.sleep(2)  # Wait for customisable options to load

                        # Now, locate and extract customisable item name and price based on the context
                        customisable_name_element = item_element.find('h3', class_='styles_itemNameText__3ZmZZ')
                        customisable_name = customisable_name_element.text.strip() if customisable_name_element else "N/A"

                        customisable_price_element = item_element.find_next('span', class_='rupee')
                        customisable_price = customisable_price_element.text.strip() if customisable_price_element else "N/A"

                        # Update the last items in the customisable lists
                        customisable_names[-1] = customisable_name
                        customisable_prices[-1] = customisable_price
                    except Exception as e:
                        print(f"Error clicking add button: {e}")
                else:
                    print("Add button not found for customisable item.")
            else:
                customisable_names.append('N/A')
                customisable_prices.append('N/A')

        driver.quit()

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        csv_file_path = f'swiggy_csv_{timestamp}.csv'
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            writer.writerow(
                ['Restaurant Name', 'Cuisines', 'Item Name', 'Item Price', 'Item Description', 'Image URL', 'Food Type',
                 'Customisable Name', 'Customisable Price'])

            # Calculate the maximum length among all lists
            max_length = max(len(item_names), len(item_prices), len(item_descriptions), len(image_urls),
                             len(food_types), len(customisable_names), len(customisable_prices))

            for i in range(max_length):
                writer.writerow([restaurant_name, restaurant_cuisines,
                                 item_names[i] if i < len(item_names) else 'N/A',
                                 item_prices[i] if i < len(item_prices) else 'N/A',
                                 item_descriptions[i] if i < len(item_descriptions) else 'N/A',
                                 image_urls[i] if i < len(image_urls) else 'N/A',
                                 food_types[i] if i < len(food_types) else 'N/A',
                                 customisable_names[i] if i < len(customisable_names) else 'N/A',
                                 customisable_prices[i] if i < len(customisable_prices) else 'N/A'])

        # print(f'Total {max_length} menu items exported to {csv_file_path}.')

        with open(csv_file_path, 'rb') as csv_file:
            response = HttpResponse(csv_file.read(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{csv_file_path}"'

        return response

    else:
        return HttpResponse('Failed to fetch the webpage.')

