from atlassian import Confluence
from bs4 import BeautifulSoup
import logging
import pandas as pd
from pandas import DataFrame



logger = logging.getLogger(__name__)

class ConfluenceManager:
    #module to connect to confluence write/get data
    def __init__(self, username, password, url):
        self.username = username
        self.password = password
        self.url = url

    # connect to confluence
    def connect(self):
        confluence = Confluence(
            url=self.url,
            username=self.username,
            password=self.password)
        return confluence
    
    #convert pandas df to html
    def get_new_html(self, pandas_df:DataFrame):
        return pandas_df.to_html(index=False)
    
    #seperate the first paragraph from the rest of the html content
    #Note: function will only work as intended if there is no other content prior to the first paragraph
    def extract_first_paragraph(self, body_content):
        line, remaining_content = body_content.split('</p>', 1)
        first_paragraph = line.split('<p>')[1]
        return first_paragraph, remaining_content
    
    
    def get_page(self, page_id:str):
        confluence = self.connect()
        return confluence.get_page_by_id(page_id=page_id, expand='body.storage')

    
    def get_page_content(self, page_id:str):
        page = self.get_page(page_id)
        return page['body']['storage']['value']
    
    
    def update_page_with_table(self, page_id:str, pandas_df:DataFrame, append_type:str='bottom', insert_below_first_paragraph:bool=False) -> None:
        """Update the selected confluence page.
        - page_id: the static url id found on your desired confluence page
        - pandas_df: the DataFrame that you wish to append to the confluence page
        - append_type: whether to append the data to the top or the bottom of the confluence page
        - insert_below_firts_paragragh: if append_type is 'top', you have the option of inserting the data below the first paragraph if True, or above the first paragraph if False
        """
        confluence = self.connect()
        logger.info("Connection Established...")
        html_table = self.get_new_html(pandas_df=pandas_df)
        current_page_details = self.get_page(page_id=page_id)
        logger.info("Page Details acquired...")
        current_content = current_page_details['body']['storage']['value']
        first_paragraph = ''
        remaining_content = current_content
        page_title = current_page_details['title']
        html_body = current_content + html_table
        
        if append_type == 'top':
            html_body = html_table + current_content
            if insert_below_first_paragraph:
                first_paragraph, remaining_content = self.extract_first_paragraph(body_content=current_content)
                html_body = first_paragraph + html_table + remaining_content
        logger.info("Writing Content...")
        confluence.update_page(page_id=page_id, title=page_title, body=html_body, representation='storage', full_width=True)
        logger.info("Page successfully updated!!!")


    def get_page_content_as_soup(self, page_id:str):
        page_content = self.get_page_content(page_id)
        return BeautifulSoup(page_content, 'html.parser')
    
    # get all tables in a page and return a list of dataframes
    def get_page_content_as_df_list(self, page_id:str) -> list:
        soup = self.get_page_content_as_soup(page_id)
        df_list = []
        for table in soup.find_all('table'):
            # use the first row as header
            df = pd.read_html(str(table), header=0)[0]
            df_list.append(df)
        return df_list