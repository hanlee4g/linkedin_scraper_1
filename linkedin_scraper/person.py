import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from .objects import Experience, Education, Scraper, Interest, Accomplishment, Contact
import os
from linkedin_scraper import selectors


class Person(Scraper):

    __TOP_CARD = "main"
    __WAIT_FOR_ELEMENT_TIMEOUT = 5

    def __init__(
        self,
        linkedin_url=None,
        name=None,
        about=None,
        experiences=None,
        educations=None,
        interests=None,
        accomplishments=None,
        company=None,
        job_title=None,
        contacts=None,
        driver=None,
        get=True,
        scrape=True,
        close_on_complete=True,
        time_to_wait_after_login=0,
    ):
        self.linkedin_url = linkedin_url
        self.name = name
        self.about = about or []
        self.experiences = experiences or []
        self.educations = educations or []
        self.interests = interests or []
        self.accomplishments = accomplishments or []
        self.also_viewed_urls = []
        self.contacts = contacts or []

        if driver is None:
            try:
                if os.getenv("CHROMEDRIVER") == None:
                    driver_path = os.path.join(
                        os.path.dirname(__file__), "drivers/chromedriver"
                    )
                else:
                    driver_path = os.getenv("CHROMEDRIVER")

                driver = webdriver.Chrome(driver_path)
            except:
                driver = webdriver.Chrome()

        if get:
            driver.get(linkedin_url)

        self.driver = driver

        if scrape:
            self.scrape(close_on_complete)

    def add_about(self, about):
        self.about.append(about)

    def add_experience(self, experience):
        self.experiences.append(experience)

    def add_education(self, education):
        self.educations.append(education)

    def add_interest(self, interest):
        self.interests.append(interest)

    def add_accomplishment(self, accomplishment):
        self.accomplishments.append(accomplishment)

    def add_location(self, location):
        self.location = location

    def add_contact(self, contact):
        self.contacts.append(contact)

    def scrape(self, close_on_complete=True):
        if self.is_signed_in():
            self.scrape_logged_in(close_on_complete=close_on_complete)
        else:
            print("you are not logged in!")

    def _click_see_more_by_class_name(self, class_name):
        try:
            _ = WebDriverWait(self.driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, class_name))
            )
            div = self.driver.find_element(By.CLASS_NAME, class_name)
            div.find_element(By.TAG_NAME, "button").click()
        except Exception as e:
            pass

    def is_open_to_work(self):
        try:
            return "#OPEN_TO_WORK" in self.driver.find_element(By.CLASS_NAME,"pv-top-card-profile-picture").find_element(By.TAG_NAME,"img").get_attribute("title")
        except:
            return False

    def get_experiences(self):
        url = os.path.join(self.linkedin_url, "details/experience")
        self.driver.get(url)
        self.focus()
        main = self.wait_for_element_to_load(by=By.TAG_NAME, name="main")
        self.scroll_to_half()
        self.scroll_to_bottom()
        main_list = self.wait_for_element_to_load(name="pvs-list__container", base=main)
        for position in main_list.find_elements(By.CLASS_NAME, "pvs-list__paged-list-item"):
            position = position.find_element(By.CSS_SELECTOR, "div[data-view-name='profile-component-entity']")
            company_logo_elem, position_details = position.find_elements(By.XPATH, "*")

            # company elem
            company_linkedin_url = company_logo_elem.find_element(By.XPATH,"*").get_attribute("href")
            if not company_linkedin_url:
                continue

            # position details
            position_details_list = position_details.find_elements(By.XPATH,"*")
            position_summary_details = position_details_list[0] if len(position_details_list) > 0 else None
            position_summary_text = position_details_list[1] if len(position_details_list) > 1 else None
            outer_positions = position_summary_details.find_element(By.XPATH,"*").find_elements(By.XPATH,"*")

            if len(outer_positions) == 4:
                position_title = outer_positions[0].find_element(By.TAG_NAME,"span").text
                company = outer_positions[1].find_element(By.TAG_NAME,"span").text
                work_times = outer_positions[2].find_element(By.TAG_NAME,"span").text
                location = outer_positions[3].find_element(By.TAG_NAME,"span").text
            elif len(outer_positions) == 3:
                if "·" in outer_positions[2].text:
                    position_title = outer_positions[0].find_element(By.TAG_NAME,"span").text
                    company = outer_positions[1].find_element(By.TAG_NAME,"span").text
                    work_times = outer_positions[2].find_element(By.TAG_NAME,"span").text
                    location = ""
                else:
                    position_title = ""
                    company = outer_positions[0].find_element(By.TAG_NAME,"span").text
                    work_times = outer_positions[1].find_element(By.TAG_NAME,"span").text
                    location = outer_positions[2].find_element(By.TAG_NAME,"span").text
            else:
                position_title = ""
                company = outer_positions[0].find_element(By.TAG_NAME,"span").text
                work_times = ""
                location = ""


            times = work_times.split("·")[0].strip() if work_times else ""
            duration = work_times.split("·")[1].strip() if len(work_times.split("·")) > 1 else None

            from_date = " ".join(times.split(" ")[:2]) if times else ""
            to_date = " ".join(times.split(" ")[3:]) if times else ""
            if position_summary_text and any(element.get_attribute("pvs-list__container") for element in position_summary_text.find_elements(By.TAG_NAME, "*")):
                inner_positions = (position_summary_text.find_element(By.CLASS_NAME,"pvs-list__container")
                                  .find_element(By.XPATH,"*").find_element(By.XPATH,"*").find_element(By.XPATH,"*")
                                  .find_elements(By.CLASS_NAME,"pvs-list__paged-list-item"))
            else:
                inner_positions = []
            if len(inner_positions) > 1:
                descriptions = inner_positions
                for description in descriptions:
                    res = description.find_element(By.TAG_NAME,"a").find_elements(By.XPATH,"*")
                    position_title_elem = res[0] if len(res) > 0 else None
                    work_times_elem = res[1] if len(res) > 1 else None
                    location_elem = res[2] if len(res) > 2 else None


                    location = location_elem.find_element(By.XPATH,"*").text if location_elem else None
                    position_title = position_title_elem.find_element(By.XPATH,"*").find_element(By.TAG_NAME,"*").text if position_title_elem else ""
                    work_times = work_times_elem.find_element(By.XPATH,"*").text if work_times_elem else ""
                    times = work_times.split("·")[0].strip() if work_times else ""
                    duration = work_times.split("·")[1].strip() if len(work_times.split("·")) > 1 else None
                    from_date = " ".join(times.split(" ")[:2]) if times else ""
                    to_date = " ".join(times.split(" ")[3:]) if times else ""

                    experience = Experience(
                        position_title=position_title,
                        from_date=from_date,
                        to_date=to_date,
                        duration=duration,
                        location=location,
                        description=description,
                        institution_name=company,
                        linkedin_url=company_linkedin_url
                    )
                    self.add_experience(experience)
            else:
                description = position_summary_text.text if position_summary_text else ""

                experience = Experience(
                    position_title=position_title,
                    from_date=from_date,
                    to_date=to_date,
                    duration=duration,
                    location=location,
                    description=description,
                    institution_name=company,
                    linkedin_url=company_linkedin_url
                )
                self.add_experience(experience)

    def get_educations(self):
        url = os.path.join(self.linkedin_url, "details/education")
        self.driver.get(url)
        self.focus()
        try: # Add error handling for the whole section
            main = self.wait_for_element_to_load(by=By.TAG_NAME, name="main")
            self.scroll_to_half()
            self.scroll_to_bottom()
            # Wait specifically for the list items to be present after scrolling
            WebDriverWait(self.driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pvs-list__paged-list-item"))
            )
            main_list = self.wait_for_element_to_load(name="pvs-list__container", base=main)

            # Find all education items within the list container
            education_items = main_list.find_elements(By.CLASS_NAME,"pvs-list__paged-list-item")
            print(f"DEBUG: Found {len(education_items)} education list items.") # Optional Debug Print

            for item in education_items: # Use 'item' instead of 'position' for clarity
                try: # Add error handling for each item
                    # Find the core entity div *relative* to the current list item
                    position_entity = item.find_element(By.XPATH,".//div[@data-view-name='profile-component-entity']")

                    # Extract children relative to the found entity
                    institution_logo_elem, position_details = position_entity.find_elements(By.XPATH,"*")

                    # company elem
                    institution_linkedin_url = None
                    try:
                        institution_linkedin_url = institution_logo_elem.find_element(By.XPATH,"*").get_attribute("href")
                    except NoSuchElementException:
                        print("DEBUG: No LinkedIn URL found for institution logo.")

                    # position details
                    position_details_list = position_details.find_elements(By.XPATH,"*")
                    position_summary_details = position_details_list[0] if len(position_details_list) > 0 else None
                    position_summary_text = position_details_list[1] if len(position_details_list) > 1 else None # Description area

                    if not position_summary_details:
                        print("DEBUG: Skipping item, could not find summary details.")
                        continue

                    outer_positions = position_summary_details.find_element(By.XPATH,"*").find_elements(By.XPATH,"*")

                    # --- Extract Details (Keep existing logic, but with safety checks) ---
                    institution_name = ""
                    degree = ""
                    times = ""
                    from_date = ""
                    to_date = ""

                    try:
                        if len(outer_positions) > 0:
                             # First span usually contains the institution name
                             institution_name = outer_positions[0].find_element(By.TAG_NAME,"span").text
                        if len(outer_positions) > 1:
                             # Second span might contain degree/field
                             degree = outer_positions[1].find_element(By.TAG_NAME,"span").text
                        if len(outer_positions) > 2:
                             # Third span might contain dates
                             times = outer_positions[2].find_element(By.TAG_NAME,"span").text
                    except NoSuchElementException:
                        print("DEBUG: Could not extract all details (name/degree/dates) using standard structure.")


                    # Parse Dates (more robustly)
                    if times:
                        parts = times.split('–') # Use '–' (en dash) which LinkedIn often uses
                        if len(parts) == 2:
                            from_date = parts[0].strip()
                            to_date = parts[1].strip()
                        elif len(parts) == 1: # Only one year listed
                             from_date = parts[0].strip()
                             to_date = parts[0].strip() # Or set to None, depending on preference

                    description = ""
                    if position_summary_text:
                         # Check for nested activities/description text
                         try:
                            description_spans = position_summary_text.find_elements(By.CSS_SELECTOR, ".pv-shared-text-with-see-more span[aria-hidden='true']")
                            if description_spans:
                                description = description_spans[0].text
                            else: # Fallback if specific span not found
                                 description = position_summary_text.text # Might include "See more"
                         except NoSuchElementException:
                             description = position_summary_text.text # Fallback

                    print(f"DEBUG: Extracted Edu: Inst='{institution_name}', Deg='{degree}', From='{from_date}', To='{to_date}'") # Optional Debug

                    # Create and add Education object
                    education = Education(
                        from_date=from_date,
                        to_date=to_date,
                        description=description.strip(), # Clean description
                        degree=degree,
                        institution_name=institution_name,
                        linkedin_url=institution_linkedin_url
                    )
                    self.add_education(education)

                except Exception as e_item:
                    print(f"[ERROR] Failed to process one education item: {e_item}")
                    # Optionally continue to the next item instead of stopping
                    continue

        except Exception as e_main:
             print(f"[ERROR] Failed during get_educations main process: {e_main}")

    def get_name_and_location(self):
        top_panel = self.driver.find_element(By.XPATH, "//*[@class='mt2 relative']")
        self.name = top_panel.find_element(By.TAG_NAME, "h1").text
        self.location = top_panel.find_element(By.XPATH, "//*[@class='text-body-small inline t-black--light break-words']").text

    def get_about(self):
        try:
            about = self.driver.find_element(By.ID,"about").find_element(By.XPATH,"..").find_element(By.CLASS_NAME,"display-flex").text
        except NoSuchElementException :
            about=None
        self.about = about

    def scrape_logged_in(self, close_on_complete=True):
        driver = self.driver
        duration = None

        root = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
            EC.presence_of_element_located(
                (
                    By.TAG_NAME,
                    self.__TOP_CARD,
                )
            )
        )
        self.focus()
        self.wait(5)

        # get name and location
        self.get_name_and_location()

        self.open_to_work = self.is_open_to_work()

        # get about
        self.get_about()
        driver.execute_script(
            "window.scrollTo(0, Math.ceil(document.body.scrollHeight/2));"
        )
        driver.execute_script(
            "window.scrollTo(0, Math.ceil(document.body.scrollHeight/1.5));"
        )

        # get experience
        self.get_experiences()

        # get education
        self.get_educations()

        driver.get(self.linkedin_url)

        # get interest
        try:

            _ = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[@class='pv-profile-section pv-interests-section artdeco-container-card artdeco-card ember-view']",
                    )
                )
            )
            interestContainer = driver.find_element(By.XPATH,
                "//*[@class='pv-profile-section pv-interests-section artdeco-container-card artdeco-card ember-view']"
            )
            for interestElement in interestContainer.find_elements(By.XPATH,
                "//*[@class='pv-interest-entity pv-profile-section__card-item ember-view']"
            ):
                interest = Interest(
                    interestElement.find_element(By.TAG_NAME, "h3").text.strip()
                )
                self.add_interest(interest)
        except:
            pass

        # get accomplishment
        try:
            _ = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[@class='pv-profile-section pv-accomplishments-section artdeco-container-card artdeco-card ember-view']",
                    )
                )
            )
            acc = driver.find_element(By.XPATH,
                "//*[@class='pv-profile-section pv-accomplishments-section artdeco-container-card artdeco-card ember-view']"
            )
            for block in acc.find_elements(By.XPATH,
                "//div[@class='pv-accomplishments-block__content break-words']"
            ):
                category = block.find_element(By.TAG_NAME, "h3")
                for title in block.find_element(By.TAG_NAME,
                    "ul"
                ).find_elements(By.TAG_NAME, "li"):
                    accomplishment = Accomplishment(category.text, title.text)
                    self.add_accomplishment(accomplishment)
        except:
            pass

        # get connections
        try:
            driver.get("https://www.linkedin.com/mynetwork/invite-connect/connections/")
            _ = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, "mn-connections"))
            )
            connections = driver.find_element(By.CLASS_NAME, "mn-connections")
            if connections is not None:
                for conn in connections.find_elements(By.CLASS_NAME, "mn-connection-card"):
                    anchor = conn.find_element(By.CLASS_NAME, "mn-connection-card__link")
                    url = anchor.get_attribute("href")
                    name = conn.find_element(By.CLASS_NAME, "mn-connection-card__details").find_element(By.CLASS_NAME, "mn-connection-card__name").text.strip()
                    occupation = conn.find_element(By.CLASS_NAME, "mn-connection-card__details").find_element(By.CLASS_NAME, "mn-connection-card__occupation").text.strip()

                    contact = Contact(name=name, occupation=occupation, url=url)
                    self.add_contact(contact)
        except:
            connections = None

        if close_on_complete:
            driver.quit()

    @property
    def company(self):
        if self.experiences:
            return (
                self.experiences[0].institution_name
                if self.experiences[0].institution_name
                else None
            )
        else:
            return None

    @property
    def job_title(self):
        if self.experiences:
            return (
                self.experiences[0].position_title
                if self.experiences[0].position_title
                else None
            )
        else:
            return None

    def __repr__(self):
        return "<Person {name}\n\nAbout\n{about}\n\nExperience\n{exp}\n\nEducation\n{edu}\n\nInterest\n{int}\n\nAccomplishments\n{acc}\n\nContacts\n{conn}>".format(
            name=self.name,
            about=self.about,
            exp=self.experiences,
            edu=self.educations,
            int=self.interests,
            acc=self.accomplishments,
            conn=self.contacts,
        )
