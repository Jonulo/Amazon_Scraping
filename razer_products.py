# import requests
from bs4 import BeautifulSoup
import json
import re
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time

headers = {
  "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36 OPR/74.0.3911.218'
}

def send_whatsapp_msg(product_info):
  print("sending whatapp msg: ", product_info)
  whatsapp_url = 'https://web.whatsapp.com/'
  options = webdriver.ChromeOptions()
  options.add_argument('--ignore-certificate-errors')
  options.add_argument('--headless')
  options.add_argument("user-data-dir=C:/Users/Georg/AppData/Local/Google/Chrome/User Data/Profile 1")
  driver_msg = webdriver.Chrome("/mnt/c/Users/Georg/Desktop/chromedriver.exe", options=options)

  driver_msg.get(whatsapp_url)
  wait = WebDriverWait(driver_msg, 60)

  target = '"Promos"'
  string = '---------- Nueva Oferta Razer! ---------- \n' + product_info['name'] + ' ('+product_info['id']+')\n' 'Bajo a: $' + str(product_info['lower_price']) + ' de: ' + product_info['price'] +'\n link: \n' + product_info['link']
 
  x_arg = '//span[contains(@title,' + target + ')]'
  group_title = wait.until(EC.presence_of_element_located((By.XPATH, x_arg)))
  group_title.click()
  inp_xpath = '//div[@class="_2_1wd copyable-text selectable-text"][@data-tab="6"]'
  input_box = wait.until(EC.presence_of_element_located((
      By.XPATH, inp_xpath)))
  input_box.click()

  input_box.send_keys(string + Keys.ENTER)
  time.sleep(1)
  driver_msg.close() 

def create_local_dataBase(products_dataBase):
  with open('razer_products.json', 'w') as f:
    f.write(json.dumps(products_dataBase))

def check_razer_prices():
  URL = 'https://www.amazon.com.mx/s?k=razer&rh=n%3A9482640011%2Cp_89%3ARazer&dc&__mk_es_MX=%C3%85M%C3%85%C5%BD%C3%95%C3%91&qid=1617120371&rnid=11790855011&ref=sr_nr_p_89_1'

  options = webdriver.ChromeOptions()
  options.add_argument('--ignore-certificate-errors')
  options.add_argument('--incognito')
  options.add_argument('--headless')
  driver = webdriver.Chrome("/mnt/c/Users/Georg/Desktop/chromedriver.exe", options=options)

  driver.get(URL)
  # WebDriverWait(driver, 60)
  page_source = driver.page_source

  soup = BeautifulSoup(page_source, 'html.parser')

  pagination_labels = soup.find_all(re.compile("^li"), class_="a-normal")
  ref_link_pagination = "https://www.amazon.com.mx"+pagination_labels[0].a['href']

  split_link = ref_link_pagination.split("&")
  format_link = split_link[0]+"&"+split_link[1]+"&"+split_link[2]+"&"+split_link[3]+"&"+split_link[4]

  try:
    print('Reading Data...')
    products_from_db = {}
    with open('razer_products.json') as f:
      read_products = f.read()
      products_from_db = json.loads(read_products)
    
    for x in range(1,6):
      print("scanning page: ",x)
      current_page_url = format_link.replace("page=2", "page="+str(x))
      print(current_page_url)

      driver_page = webdriver.Chrome("/mnt/c/Users/Georg/Desktop/chromedriver.exe", options=options)
      driver_page.get(current_page_url)
      current_page_source = driver_page.page_source

      soup_link = BeautifulSoup(current_page_source, 'html.parser')
      all_razer_products = soup_link.find_all(re.compile("^div"), class_="s-result-item")

      for product in all_razer_products:
        new_product_in_db = {}
        new_product_id = product.attrs.get("data-asin", None)
        new_product_price = product.find('span', class_="a-offscreen")

        new_product_info = product.find_all('h2', class_="a-size-mini")
        new_product_name = ""
        new_product_link = ""
        for prod in new_product_info:
          new_product_name = prod.span.string
          new_product_link = prod.a['href']

        if new_product_id is not None and new_product_id != "" and new_product_price is not None and new_product_name is not None:
          if new_product_id in products_from_db:
            local_product = products_from_db.get(new_product_id)

            new_product_price_for_compare = float(new_product_price.string[1:].replace(',',''))
            local_product_price_for_compare = float(local_product['price'][1:].replace(',',''))

            is_offer = local_product_price_for_compare - ((local_product_price_for_compare * 10) / 100)
            if new_product_price_for_compare <= is_offer:
              if 'lower_price' in local_product:
                if local_product['lower_price'] > new_product_price_for_compare:
                  local_product['lower_price'] = new_product_price_for_compare
                  print("el producto: ", local_product['name'], "bajo del lower_precio: $", local_product['lower_price'], "a: $", new_product_price_for_compare)
                  send_whatsapp_msg(local_product)
              else:
                local_product['lower_price'] = new_product_price_for_compare
                send_whatsapp_msg(local_product)
                print("el producto: ", local_product['name'], "bajo del precio: $", local_product_price_for_compare, "a: $", new_product_price_for_compare)

          else:
            razer_product['page_num'] = x
            new_product_in_db['id'] = new_product_id
            new_product_in_db['name'] = new_product_name
            new_product_in_db['link'] = "https://www.amazon.com.mx"+new_product_link
            new_product_in_db['price'] = new_product_price.string
            products_from_db[new_product_id] = new_product_in_db
            print("new product added: ", new_product_name)
      driver_page.close()
    time.sleep(1)
    driver_page.quit()

    create_local_dataBase(products_from_db)
    print("---------------")
    print("price scanner finished")
    print("---------------")

  except IOError:
    print('Creating File...')
    
    final_product = {}

    for x in range(1,6):
      print("scanning page: ",x)
      current_page_url = format_link.replace("page=2", "page="+str(x))
      print(current_page_url)
      
      driver_page = webdriver.Chrome("/mnt/c/Users/Georg/Desktop/chromedriver.exe", options=options)
      driver_page.get(current_page_url)
      current_page_source = driver_page.page_source

      soup_link = BeautifulSoup(current_page_source, 'html.parser')
      all_razer_products = soup_link.find_all(re.compile("^div"), class_="s-result-item")

      for product in all_razer_products:
        razer_product = {}
        product_id = product.attrs.get("data-asin", None)
        product_price = product.find('span', class_="a-offscreen")

        product_info = product.find_all('h2', class_="a-size-mini")
        product_name = ""
        product_link = ""
        for prod in product_info:
          product_name = prod.span.string
          product_link = prod.a['href']

        if product_name is not None and product_price is not None and product_id is not None:
          razer_product['page_num'] = x
          razer_product['id'] = product_id
          razer_product['name'] = product_name
          razer_product['link'] = "https://www.amazon.com.mx"+product_link
          razer_product['price'] = product_price.string

          final_product[product_id] = razer_product
      driver_page.close()
    time.sleep(1)
    driver_page.quit()

    if not bool (final_product):
      print("Error creating local Data Base")
    else:
      create_local_dataBase(final_product)
      print(final_product)
      print("Local dataBase created!")
  driver.quit()

# while(True):
#   check_razer_prices()
#   time.sleep(1800)

check_razer_prices()