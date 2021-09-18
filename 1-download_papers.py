#!/usr/bin/env python
# coding: utf-8

# # Dev: Papers IDs collector
# 
# 
# ### References
# 
# - [arXiv.org](https://arxiv.org/)
# - [arXiv API-Homepage](https://pypi.org/project/arxiv/)
# - [arXiv API-Documentation](http://lukasschwab.me/arxiv.py/index.html)

import os
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
import warnings
warnings.filterwarnings('ignore')


## environment variables ##

# urls dictionary
durls = {}
# url: Computer Science (cs)
#durls['cs'] = 'https://arxiv.org/search/advanced?advanced=&terms-0-operator=AND&terms-0-term=&terms-0-field=title&classification-computer_science=y&classification-physics_archives=all&classification-include_cross_list=include&date-filter_by=all_dates&date-year=&date-from_date=&date-to_date=&date-date_type=submitted_date&abstracts=show&size=200&order=-announced_date_first&start=0'
# url: Mathematics (math)
durls['math'] = 'https://arxiv.org/search/advanced?advanced=&terms-0-operator=AND&terms-0-term=&terms-0-field=title&classification-mathematics=y&classification-physics_archives=all&classification-include_cross_list=include&date-filter_by=all_dates&date-year=&date-from_date=&date-to_date=&date-date_type=submitted_date&abstracts=show&size=200&order=-announced_date_first&start=0'
# url: Statistics (stat)
durls['stat'] = 'https://arxiv.org/search/advanced?advanced=&terms-0-operator=AND&terms-0-term=&terms-0-field=title&classification-physics_archives=all&classification-statistics=y&classification-include_cross_list=include&date-filter_by=all_dates&date-year=&date-from_date=&date-to_date=&date-date_type=submitted_date&abstracts=show&size=200&order=-announced_date_first&start=0'

required_categories = ['math.ST', 'stat.ME', 'stat.AP', 'stat.CO', 'cs.LG', 'stat.ML', 'cs.AI', 'math.PR']
folder_output = 'datasets'


## functions ##


# check if two list of categories have any common element
def is_category(cat_paper:list, cat_required: list):
    cat_inter = list(set(cat_paper) & set(cat_required))
    return len(cat_inter) > 0


## parse papers information in a page of the advanced query search
def parser_page(url:str, verbose:bool = False)->pd.DataFrame:
    # initialize
    col_x = ['paper_id', 'categories', 'submission_date', 'title', 'authors', 'abstract']

    # download html content
    try:
        # get request
        reqs = requests.get(url)
        # get html page
        soup = BeautifulSoup(reqs.text, 'lxml')
    except Exception as e:
        print(f'[error] It was not possible download the html content of this url: "{url}"')
        print(str(e))
        return None

    # initialize
    records = list() 

    # loop of results
    for tag in soup.find_all("li", {"class": "arxiv-result"}):

        # parse categories
        tag_d = tag.find_all("div", {"class": "tags is-inline-block"})[0]
        categories = [it.rstrip().lstrip() for it in tag_d.text.split('\n') if it != '']
        if verbose:
            print("\n{0}: {1}".format(tag_d.name, categories))   
             
        # only continue if is a required paper by category
        if is_category(categories, required_categories):

            # parse paper id
            tag_a = tag.find_all("a")[0]
            paper_id = tag_a.text.replace('arXiv:', '').rstrip().lstrip()
            if verbose:
                print("{0}: {1}".format(tag_a.name, paper_id))

            # parse submission date
            tag_p = tag.find_all("p")[4]
            sdate = tag_p.text.split(';')[0].replace('Submitted', '').rstrip().lstrip()
            dt = datetime.strptime(sdate, '%d %B, %Y')
            submission_date = date(dt.year, dt.month, dt.day)
            if verbose:
                print("{0}: {1}".format(tag_p.name, submission_date))

            # parse title
            tag_p = tag.find_all("p")[1]
            title = tag_p.text.replace('\n','').rstrip().lstrip()
            if verbose:
                print("{0}: {1}".format(tag_p.name, title))
                
            # parse authors
            tag_p = tag.find_all("p")[2]
            authors = [a.rstrip().lstrip() for a in tag_p.text.replace('Authors:', '').replace('\n','').split(',')]
            if verbose:
                print("{0}: {1}".format(tag_p.name, authors))

            # parse abstract
            tag_s = tag.find_all("span", {"class": "abstract-full has-text-grey-dark mathjax"})[0]
            abstract = tag_s.contents[0].replace('\n','').rstrip().lstrip()
            if verbose:
                print("{0}: {1}".format(tag_s.name, abstract))

            # append if any common cat and if submission date is in the required period
            records.append([paper_id, categories, submission_date, title, authors, abstract])
        else:
            if verbose:
                print("discarted because is not required.")

    # store in a df
    df = pd.DataFrame(records, columns = col_x)
    if verbose:
        print(f'\nFinally was parsed {len(df)} papers.')

    # return
    return df


## get size of page
def get_page_size(url:str)->int:
    try:
        return int([iu for iu in url.split('&') if 'size' in iu][0].replace('size=', ''))
    except:
        print('[error] It is not available "size" tag in this url.')
        return None

    
## get next page
def next_paginate(url:str, size:int)->str:
    try:
        start = int([iu for iu in url.split('&') if 'start' in iu][0].replace('start=', ''))
        return url.replace(f'start={start}', f'start={start + size}')
    except:
        print('[error] It is not available "start" tag in this url.')
        return None

    
## check if url is valid
def is_valid_url(url:str)->bool:
    if 'size' in url and 'start=0' in url and '=all' in url and 'abstracts=show' in url and 'include_cross_list=include' in url:
        return True
    else:
        return False
    

## parse papers information in a N pages of the advanced query search
def parser_pages(url:str, dti, dtf, max_num_pages:int = 200000, verbose:bool = False)->pd.DataFrame:    
    # check if a valid url
    if is_valid_url(url):
        print('It is a valid url.')
    else:
        print('[error] It is not a valid url.')
        return None

    # get page size
    size = get_page_size(url)
    # initialize
    num_page = 1
    # loop
    while num_page <= max_num_pages:
        # parse
        idf = parser_page(url, verbose = verbose)
        # validate
        if idf is None:
            print('Stop loop!')
            if num_page == 1:
                return None
            else:
                break
        else:
            # append
            if num_page == 1:
                df = idf.copy()
            else:
                df = df.append(idf)
            # display
            idti = np.nanmin(df.submission_date)
            print(f'--> Page {num_page} - total num records = {len(df)} / older date: {idti.strftime("%Y-%m-%d")}')
            # clean
            del idf, idti
            # get next page url
            url = next_paginate(url, size)
        # add counter
        num_page += 1
    # return
    return df


## main function
def main(dti, dtf):
    # loop of urls
    for area in durls.keys():
        # display
        print(f'\nSTART TO PARSE: "{area}"')
        # current time
        tic = datetime.now()        
        # parse urls
        data = parser_pages(durls[area], dti, dtf, verbose = False)
        # save outputs
        sdt_now = datetime.now().strftime("%Y%m%d_%H%M%S")
        path_output = os.path.join(folder_output, f'papers-{area}-{sdt_now}.csv')
        data.to_csv(path_output, index = False)
        # calculate time of processing
        toc = datetime.now()
        tictoc = ((toc-tic).seconds)/60. # minutes
        print ("\nProcess start: %s"%tic)
        print ("Process finish: %s"%toc)
        print ("Process time spent %s minutes"%tictoc)
    # return
    return None


## main ##

if __name__ == '__main__':

    # ## arguments
    dti = None
    dtf = None
    # launch
    main(dti, dtf)






