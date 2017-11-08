import os
import re
import time

from pattern.web import URL, DOM
from selenium import webdriver


class PinterestCrawler(object):
    def __init__(self, search_key=''):
        """ Pinterest image search class
            Args:
                search_key to be entered.

        """
        if type(search_key) == str:
            ## convert to list even for one search keyword to standalize the pulling.
            self.g_search_key_list = [search_key]
        elif type(search_key) == list:
            self.g_search_key_list = search_key
        else:
            print 'keyword not of type str or list'
            raise

        self.g_search_key = ''

        ## user options
        self.image_dl_per_search = 200  # by default (if not explicitly set in set_num_image_to_dl function), this number of images will be downloaded

        ## url construct string text
        self.prefix_of_search_url = "https://pl.pinterest.com/search/pins/?q="
        self.target_url_str = ''

        ## storage
        self.pic_url_list = []
        self.pic_info_list = []

        ## file and folder path

        #save to current dir "."
        self.folder_main_dir_prefix = r'.'

    def reformat_search_for_spaces(self):
        """
            Method call immediately at the initialization stages
            get rid of the spaces and replace by the "+"
            Use in search term. Eg: "Cookie fast" to "Cookie+fast"

            steps:
            strip any lagging spaces if present
            replace the self.g_search_key
        """
        self.g_search_key = self.g_search_key.rstrip().replace(' ', '+')

    def set_num_image_to_dl(self, num_image):
        """ Set the number of image to download. Set to self.image_dl_per_search.
            Args:
                num_image (int): num of image to download.
        """
        self.image_dl_per_search = num_image

    def get_searchlist_fr_file(self, filename):
        """Get search list from filename. Ability to add in a lot of phrases.
            Will replace the self.g_search_key_list
            Args:
                filename (str): full file path
        """
        with open(filename, 'r') as f:
            self.g_search_key_list = f.readlines()

    def formed_search_url(self):
        ''' Form the url either one selected key phrases or multiple search items.
            Get the url from the self.g_search_key_list
            Set to self.sp_search_url_list
        '''
        self.reformat_search_for_spaces()
        self.target_url_str = self.prefix_of_search_url + self.g_search_key

    def multi_search_download(self):
        """ Mutli search download"""
        self.create_folder()
        for indiv_search in self.g_search_key_list:
            self.pic_url_list = []
            self.pic_info_list = []
            self.g_search_key = indiv_search
            self.formed_search_url()
            self.retrieve_source_fr_html()
            self.extract_pic_url()
            indinv_search_dir_path = os.path.join(self.gs_raw_dirpath, self.g_search_key.replace("\n", ""))
            if not os.path.exists(indinv_search_dir_path):
                os.makedirs(indinv_search_dir_path)
            self.downloading_all_photos()
            self.save_infolist_to_file()

    def retrieve_source_fr_html(self):
        """ Make use of selenium. Retrieve from html table using pandas table.

        """

        options = webdriver.ChromeOptions()
        options.add_argument("user-data-dir=C:\Users\pan\AppData\Local\Google\Chrome\User Data")  # Path to your chrome profile
        driver = webdriver.Chrome(chrome_options=options)

        driver.get(self.target_url_str)

        ## wait for log in then get the page source.
        try:
            driver.execute_script("window.scrollTo(0, 10000000)")
            time.sleep(1)
            self.temp_page_source = driver.page_source
            # driver.find_element_by_tag_name('img').click()  # ok

            #here we assume that one scroll is equal to gathering 20 new images
            for i in range(0, int(self.image_dl_per_search/20)):
                time.sleep(2)
                driver.execute_script("window.scrollTo(0, 10000000)")

        except Exception as e:
            print e
            print 'not able to find'
            driver.quit()

        self.page_source = driver.page_source

        driver.close()

    def extract_pic_url(self):
        """ extract all the raw pic url in list

        """
        dom = DOM(self.page_source)
        tag_list = dom('img')

        #we start for lopp from 1, becuase 0 index contains some crap image (connected with username account?)
        for tag in tag_list[1:self.image_dl_per_search+1]:
            tar_str = re.search("3x,.*jpg", tag.source)
            tar_str = tar_str.group(0).replace("3x, ", "")
            try:
                self.pic_url_list.append(tar_str)
            except:
                print 'error parsing', tag

    def create_folder(self):
        """
            Create a folder to put the log data segregate by date

        """
        self.gs_raw_dirpath = os.path.join(self.folder_main_dir_prefix, time.strftime("_%d_%b%y", time.localtime()))
        if not os.path.exists(self.gs_raw_dirpath):
            os.makedirs(self.gs_raw_dirpath)

    def downloading_all_photos(self):
        """ download all photos to particular folder

        """
        print("For " + str(self.g_search_key) + " I've found " + str(len(self.pic_url_list)) + "photos. Now i will download them!")
        self.create_folder()
        pic_counter = 1
        for url_link in self.pic_url_list:
            print pic_counter
            pic_prefix_str = self.g_search_key + str(pic_counter)
            try:
                self.download_single_image(url_link.encode(), pic_prefix_str)
                pic_counter = pic_counter + 1
            except:
                continue

    def download_single_image(self, url_link, pic_prefix_str):
        """ Download data according to the url link given.
            Args:
                url_link (str): url str.
                pic_prefix_str (str): pic_prefix_str for unique label the pic
        """
        self.download_fault = 0
        file_ext = os.path.splitext(url_link)[1]  # use for checking valid pic ext
        temp_filename = pic_prefix_str + file_ext
        temp_filename_full_path = os.path.join(self.gs_raw_dirpath, self.g_search_key, temp_filename)

        valid_image_ext_list = ['.jpg']  # not comprehensive

        url = URL(url_link)
        #if url.redirect:
        #    return  # if there is re-direct, return

        if file_ext not in valid_image_ext_list:
            return  # return if not valid image extension

        f = open(temp_filename_full_path, 'wb')
        print url_link
        self.pic_info_list.append(pic_prefix_str + ': ' + url_link)
        try:
            f.write(url.download())  # if have problem skip
        except:
            # if self.__print_download_fault:
            print 'Problem with processing this data: ', url_link
            self.download_fault = 1
        f.close()

    def save_infolist_to_file(self):
        """ Save the info list to file.

        """
        temp_filename_full_path = os.path.join(self.gs_raw_dirpath, self.g_search_key, self.g_search_key + '_info.txt')

        with  open(temp_filename_full_path, 'w') as f:
            for n in self.pic_info_list:
                f.write(n)
                f.write('\n')


if __name__ == '__main__':
    crawler = PinterestCrawler('')  # leave blank if get the search list from file
    searchlist_filename = r'search_list.txt'
    crawler.set_num_image_to_dl(3000)  # number of images to download per single search
    crawler.get_searchlist_fr_file(searchlist_filename)  # replace the search list
    crawler.multi_search_download()
