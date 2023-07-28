#!/usr/bin/env python
# coding: utf-8

# In[11]:


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time
import pygsheets
import gspread
from bs4 import BeautifulSoup
import json

username = 'temeshev16.02@gmail.com'
password = 'Miras010101'


# In[12]:


def login(driver: webdriver):
    login_url = r'https://royalacetennisclub.s20.online/'
    driver.get(login_url)

    # Find the username and password input fields using their IDs and fill them in
    username_input = driver.find_element(By.ID, 'loginform-username')
    password_input = driver.find_element(By.ID, 'loginform-password')

    username_input.send_keys(username)
    password_input.send_keys(password)

    # You can also simulate pressing the 'Enter' key to submit the form
    password_input.send_keys(Keys.ENTER)

    # If the website has a login button, you can click it instead of simulating 'Enter'
    # login_button = driver.find_element_by_id('login-button-id')
    # login_button.click()

    # Optionally, you can wait for a moment to see if the login is successful
    driver.implicitly_wait(5)
    return True

def next_page(driver: webdriver):
    try:
        # Find the "Next" button in the pagination and click on the associated "a" tag
        pagination_list = driver.find_element(By.CLASS_NAME, 'pagination')
        next_button = pagination_list.find_element(By.CLASS_NAME, 'next')
        next_button_a = next_button.find_element(By.TAG_NAME, 'a')
        next_button_a.click()
        return True
    except:
        print('You are already on the last page')
        return False

def find_first_number_index(s):
    try:
        index = s.index(next(filter(str.isdigit, s)))
        return index
    except StopIteration:
        return -1
    
def split_FCs(line):
    f_ind = find_first_number_index(line)
    fcs = line[:f_ind]
    s_ind = line.find('(')
    age = line[f_ind:s_ind]
    date_of_birth = line[s_ind+1:len(line) - 1]
    return fcs, age, date_of_birth

def find_responsible(line):
    return line[:line.find('Не задано')]

def find_left(line):
    return line[:line.find('/')], line[line.find('/')+1:]

def get_data(driver: webdriver):
    table_data = driver.find_element(By.CLASS_NAME, 'crm-table')
    table_html = table_data.get_attribute('outerHTML')
    
    df = pd.read_html(table_html)[0]

    labels = [
        'ID', 'ФИО', 'Заказчик', 'Возраст', 'Дата рождения', 'Ответственный', 'Группы', 
        'Статус обучения', 'Источник', "Общий остаток (деньги)", "Бонусный счёт", "Общий остаток (уроки)", 
        "Дата истечения оплаты", "Дата посл. посещения", "Дата след. посещения", "Предмет", "Уровень",
        "Отв. педагог", "Телефон", "E-mail", "Адрес", "Website", "Примечание", "Абонементы", "Номер договоров",
        "Добавлен", "Причина потери", "Активные группы", "Активные абонементы", "Пол", "Статус клиента"
        ]

    res = pd.DataFrame(columns=labels)
    res['ID'] = df['ID']

    fcs, age, date_of_birth = [], [], []
    for f, a, d in df['ФИО'].apply(split_FCs):
        fcs.append(f)
        age.append(a)
        date_of_birth.append(d)

    res['ФИО'] = pd.Series(fcs)
    res.insert(2, "Тип заказчика", "Физ.лицо")
    res['Заказчик'] = pd.Series(fcs)
    res['Возраст'] = pd.Series(age)
    res['Дата рождения'] = pd.Series(date_of_birth)
    res['Ответственный'] = df['Ответственный'].apply(find_responsible)
    res['Группы'] = df['Группы']
    res['Статус обучения'] = df['Статус обучения']
    res['Источник'] = df['Источник']
    
    money, number = [], []
    for m, n in df['Общий остаток'].apply(find_left):
        money.append(m)
        number.append(n)

    res['Общий остаток (деньги)'] = pd.Series(money)
    res['Бонусный счёт'] = df['Бонусный счет']
    res['Общий остаток (уроки)'] = pd.Series(number)
    res['Дата истечения оплаты'] = df['Ожидаем']
    res['Дата посл. посещения'] = df['Дата посл. посещ.']
    res['Дата след. посещения'] = pd.Series()
    res['Предмет'] = pd.Series()
    res['Уровень'] = pd.Series()
    res['Отв. педагог'] = df['Отв. педагог']
    res['Телефон'] = "'" + df['Контакты']
    res['E-mail'] = pd.Series()
    res['Адрес'] = pd.Series()
    res['Website'] = pd.Series()
    res['Примечание'] = df['Примечание']
    res['Абонементы'] = df['Абонементы']
    res['Номер договоров'] = pd.Series()
    res['Добавлен'] = df['Добавлен']
    res['Причина потери'] = df['Причина потери']
    res['Активные группы'] = df['Активные группы']
    res['Активные абонементы'] = df['Активные абонементы']
    res['Пол'] = df['Пол']
    # res['Статус клиента'] = df['Статус Клиента']
    res = res.fillna('')
    
    return res


# In[13]:


# Groups
driver = webdriver.Firefox()
groups = pd.DataFrame()
time.sleep(3)

login(driver)
time.sleep(3)

print(driver.get(r'https://royalacetennisclub.s20.online/company/1/customer/index'))
groups = pd.concat([groups, get_data(driver)])


while next_page(driver):
    time.sleep(3)
    groups = pd.concat([groups, get_data(driver)])
    i += 1

    
time.sleep(3)


with open('clients.json', 'w', encoding='utf-8') as file:
    groups.to_json(file, orient='table', force_ascii=False)


# In[14]:


gc = pygsheets.authorize(service_file='cred.json')
spreadsheet = gc.open_by_url('https://docs.google.com/spreadsheets/d/1IxjBLSUHA5VQoWouFJ9_stmCyEOpgXE6uab9zVGh1IQ')

sheet = spreadsheet[1]

# Clear the existing data from the sheet (optional)
sheet.clear()

# Paste the DataFrame data into the sheet starting from cell A1
sheet.set_dataframe(groups, start='A1')


# In[ ]:




