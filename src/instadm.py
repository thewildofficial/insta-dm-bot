from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager as CM
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from random import randint, uniform
from time import time, sleep
import logging
import pandas as pd
import sqlite3

DEFAULT_IMPLICIT_WAIT = 1


class InstaDM(object):

    def __init__(self, username, password, headless=True, instapy_workspace=None, profileDir=None):
        self.selectors = {
            "home_to_login_button": "//button[text()='Log in']",
            "username_field": "username",
            "password_field": "password",
            "button_login": "//button/*[text()='Log in']",
            "login_check": "//*[@aria-label='Home'] | //button[text()='Save Info'] | //button[text()='Not Now']",
            "search_user": "queryBox",
            "select_user": "//*[contains(text(), '')]",
            "name": "((//div[@aria-labelledby]/div/span//img[@data-testid='user-avatar'])[1]//..//..//..//div[2]/div[2]/div)[1]",
            "next_button": "//*[contains(text(), 'Next')]",
            "textarea": "//textarea[@placeholder]",
            "send": "//button[text()='Send']"
        }

        # Selenium config
        options = webdriver.ChromeOptions()

        if profileDir:
            options.add_argument("user-data-dir=profiles/" + profileDir)

        if headless:
            options.add_argument("--headless")
        mobile_emulation = {
            "userAgent": 'Mozilla/5.0 (Linux; Android 10.0; iPhone Xs Max Build/IML74K) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/91.0.4472.77 Mobile Safari/535.19'
        }
        options.add_experimental_option("mobileEmulation", mobile_emulation)
        options.add_argument("--log-level=3")

        self.driver = webdriver.Chrome(executable_path=CM().install(), options=options)
        #self.driver = webdriver.Chrome(executable_path='/Users/aban/.wdm/drivers/chromedriver/mac64/119.0.6045.105/chromedriver-mac-arm64/chromedriver', options=options)
        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(414, 936)

        # Instapy init DB
        self.instapy_workspace = instapy_workspace
        self.conn = None
        self.cursor = None
        if self.instapy_workspace is not None:
            self.conn = sqlite3.connect(
                self.instapy_workspace + "InstaPy/db/instapy.db")
            self.cursor = self.conn.cursor()

            cursor = self.conn.execute("""
                SELECT count(*)
                FROM sqlite_master
                WHERE type='table'
                AND name='message';
            """)
            count = cursor.fetchone()[0]

            if count == 0:
                self.conn.execute("""
                    CREATE TABLE "message" (
                        "username"    TEXT NOT NULL UNIQUE,
                        "message"    TEXT DEFAULT NULL,
                        "sent_message_at"    TIMESTAMP
                    );
                """)

        try:
            self.login(username, password)
        except Exception as e:
            logging.error(e)
            print(str(e))

    def login(self, username, password):
        # homepage
        self.driver.get('https://www.instagram.com/accounts/login/')
        self.__random_sleep__(3, 5)

        # login
        logging.info(f'Login with {username}')
        self.__scrolldown__()
        if not self.__wait_for_element__(self.selectors['username_field'], 'name', 10):
            print('Login Failed: username field not visible')
        else:
            self.driver.find_element_by_name(
                self.selectors['username_field']).send_keys(username)
            self.driver.find_element_by_name(
                self.selectors['password_field']).send_keys(password)
            self.__get_element__(
                self.selectors['button_login'], 'xpath').click()
            self.__random_sleep__()
            if self.__wait_for_element__(self.selectors['login_check'], 'xpath', 10):
                print(f' {username}: Login Successful')
            else:
                print(f'Login Failed ({username}): Incorrect credentials')

    def createCustomGreeting(self, greeting):
        # Get username and add custom greeting
        if self.__wait_for_element__(self.selectors['name'], "xpath", 10):
            user_name = self.__get_element__(
                self.selectors['name'], "xpath").text
            if user_name:
                greeting = greeting + " " + user_name + ", \n\n"
        else:
            greeting = greeting + ", \n\n"
        return greeting

    def typeMessage(self, user, message):
        self.__random_sleep__()

        for line in message:
            self.driver.switch_to.active_element.send_keys(line)
            self.driver.switch_to.active_element.send_keys(Keys.SHIFT + Keys.ENTER)
        self.driver.switch_to.active_element.send_keys(Keys.RETURN)
        self.__random_sleep__()




    def sendMessage(self, user, message, greeting=None, file=None):
        logging.info(f'Send message to {user}')
        self.driver.get('https://www.instagram.com/direct/new/?hl=en')
        self.__random_sleep__(1, 2)

        try:
            self.__wait_for_element__(self.selectors['search_user'], "name")
            self.__type_slow__(self.selectors['search_user'], "name", user)
            self.__random_sleep__(1, 2)

            if greeting != None:
                greeting = self.createCustomGreeting(greeting)

            # Select user from list
            elements = self.driver.find_elements_by_xpath(f"//*[contains(text(), '{user}')]")
            #print(elements)
            if elements and len(elements) > 0:
                elements[0].click()
                self.__get_element__(self.selectors['next_button'], 'xpath').click()
                self.__random_sleep__()



                # Click the button if it exists
                try:
                    # Find the button with text "Not Now"
                    not_now_button = self.driver.find_element_by_xpath("//button[contains(text(), 'Not Now')]")
                    not_now_button.click()
                    self.driver.refresh()
                except:
                    pass
                
                if greeting != None:
                    self.typeMessage(user, greeting + message)
                else:
                    self.typeMessage(user, message)

                if self.conn is not None:
                    self.cursor.execute(
                        'INSERT INTO message (username, message) VALUES(?, ?)', (user, message))
                    self.conn.commit()
                # update the CSV file with Reached? = Yes
                if file is None:
                    raise ValueError("CSV file reference not provided")
                else:
                    df = pd.read_csv('infos/' + file)
                    df.loc[df['Username'] == user, 'Reached?'] = 'Yes'
                    df.to_csv('infos/' + file, index=False)
                self.__random_sleep__(2, 3)
                return True

            # In case user has changed his username or has a private account
            else:
                print(f'User {user} not found! Removing from list...')
                # remove the username from the CSV file
                if file != None:
                    df = pd.read_csv('infos/' + file)
                    df = df[df.Username != user]
                    df.to_csv('infos/' + file, index=False)
                return False

        except Exception as e:
            logging.error(e)
            return False

    def sendGroupMessage(self, users, message):
        logging.info(f'Send group message to {users}')
        print(f'Send group message to {users}')
        self.driver.get('https://www.instagram.com/direct/new/?hl=en')
        self.__random_sleep__(5, 7)

        try:
            usersAndMessages = []
            for user in users:
                if self.conn is not None:
                    usersAndMessages.append((user, message))

                self.__wait_for_element__(
                    self.selectors['search_user'], "name")
                self.__type_slow__(self.selectors['search_user'], "name", user)
                self.__random_sleep__()

                # Select user from list
                elements = self.driver.find_elements_by_xpath(
                    self.selectors['select_user'].format(user))
                if elements and len(elements) > 0:
                    elements[0].click()
                    self.__random_sleep__()
                else:
                    print(f'User {user} not found! Skipping.')
                    

            self.typeMessage(user, message)

            if self.conn is not None:
                self.cursor.executemany("""
                    INSERT OR IGNORE INTO message (username, message) VALUES(?, ?)
                """, usersAndMessages)
                self.conn.commit()
            self.__random_sleep__(50, 60)

            return True

        except Exception as e:
            logging.error(e)
            return False

    def sendGroupIDMessage(self, chatID, message):
        logging.info(f'Send group message to {chatID}')
        print(f'Send group message to {chatID}')
        self.driver.get('https://www.instagram.com/direct/inbox/')
        self.__random_sleep__(5, 7)

        # Definitely a better way to do this:
        actions = ActionChains(self.driver)
        actions.send_keys(Keys.TAB*2 + Keys.ENTER).perform()
        actions.send_keys(Keys.TAB*4 + Keys.ENTER).perform()

        if self.__wait_for_element__(f"//a[@href='/direct/t/{chatID}']", 'xpath', 10):
            self.__get_element__(
                f"//a[@href='/direct/t/{chatID}']", 'xpath').click()
            self.__random_sleep__(3, 5)

        try:
            usersAndMessages = [chatID]

            if self.__wait_for_element__(self.selectors['textarea'], "xpath"):
                self.__type_slow__(
                    self.selectors['textarea'], "xpath", message)
                self.__random_sleep__()

            if self.__wait_for_element__(self.selectors['send'], "xpath"):
                self.__get_element__(self.selectors['send'], "xpath").click()
                self.__random_sleep__(3, 5)


            if self.conn is not None:
                self.cursor.executemany("""
                    INSERT OR IGNORE INTO message (username, message) VALUES(?, ?)
                """, usersAndMessages)
                self.conn.commit()
            self.__random_sleep__(50, 60)

            return True

        except Exception as e:
            logging.error(e)
            return False

    def __get_element__(self, element_tag, locator):
        """Wait for element and then return when it is available"""
        try:
            locator = locator.upper()
            dr = self.driver
            if locator == 'ID' and self.is_element_present(By.ID, element_tag):
                return WebDriverWait(dr, 15).until(lambda d: dr.find_element_by_id(element_tag))
            elif locator == 'NAME' and self.is_element_present(By.NAME, element_tag):
                return WebDriverWait(dr, 15).until(lambda d: dr.find_element_by_name(element_tag))
            elif locator == 'XPATH' and self.is_element_present(By.XPATH, element_tag):
                return WebDriverWait(dr, 15).until(lambda d: dr.find_element_by_xpath(element_tag))
            elif locator == 'CSS' and self.is_element_present(By.CSS_SELECTOR, element_tag):
                return WebDriverWait(dr, 15).until(lambda d: dr.find_element_by_css_selector(element_tag))
            else:
                logging.info(f"Error: Incorrect locator = {locator}")
        except Exception as e:
            logging.error(e)
        logging.info(f"Element not found with {locator} : {element_tag}")
        return None

    def is_element_present(self, how, what):
        """Check if an element is present"""
        try:
            self.driver.find_element(by=how, value=what)
        except NoSuchElementException:
            return False
        return True

    def __wait_for_element__(self, element_tag, locator, timeout=30):
        """Wait till element present. Max 30 seconds"""
        result = False
        self.driver.implicitly_wait(0)
        locator = locator.upper()
        for i in range(timeout):
            initTime = time()
            try:
                if locator == 'ID' and self.is_element_present(By.ID, element_tag):
                    result = True
                    break
                elif locator == 'NAME' and self.is_element_present(By.NAME, element_tag):
                    result = True
                    break
                elif locator == 'XPATH' and self.is_element_present(By.XPATH, element_tag):
                    result = True
                    break
                elif locator == 'CSS' and self.is_element_present(By.CSS_SELECTORS, element_tag):
                    result = True
                    break
                else:
                    logging.info(f"Error: Incorrect locator = {locator}")
            except Exception as e:
                logging.error(e)
                print(f"Exception when __wait_for_element__ : {e}")

            sleep(1 - (time() - initTime))
        else:
            print(
                f"Timed out. Element not found with {locator} : {element_tag}")
        self.driver.implicitly_wait(DEFAULT_IMPLICIT_WAIT)
        return result

    def __type_slow__(self, element_tag, locator, input_text=''):
        """Type the given input text"""
        try:
            self.__wait_for_element__(element_tag, locator, 5)
            element = self.__get_element__(element_tag, locator)
            actions = ActionChains(self.driver)
            actions.click(element).perform()
            for s in input_text:
                element.send_keys(s)
                sleep(uniform(0.005, 0.02))

        except Exception as e:
            logging.error(e)
            print(f'Exception when __typeSlow__ : {e}')

    def __random_sleep__(self, minimum=2, maximum=7):
        t = randint(minimum, maximum)
        logging.info(f'Wait {t} seconds')
        sleep(t)

    def __scrolldown__(self):
        self.driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")

    def teardown(self):
        self.driver.close()
        self.driver.quit()
