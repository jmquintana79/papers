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
from datetime import datetime
import arxiv
from datetime import datetime
import ray
import warnings
warnings.filterwarnings('ignore')



# ## arguments
#required_categories = ['math.ST', 'stat.ME', 'stat.AP', 'stat.CO', 'cs.LG', 'stat.ML', 'cs.AI']
required_categories = ['cs.LG'] # , 'stat.ML', 'cs.AI'
folder_output = 'datasets'

# init principal time counter
tic_p = datetime.now()



# ## collect required IDs

# loop of categories
for cat in required_categories:
    # display
    print(f'--> collecting category "{cat}"')

    # query
    print('[info] Query of searching for papers ...')
    search = arxiv.Search(query=f"cat:{cat}", sort_by=arxiv.SortCriterion.SubmittedDate)

    ## init ray
    ray.init()

    @ray.remote
    def return_out(paper):
        try:
            return (paper.get_short_id(), paper.published)
        except:
            return np.nan, np.nan


    # init time counter
    tic = datetime.now()
    # collect papers ids
    print('[info] Collecting information of papers ...')
    #outs = [return_out.remote(paper) for paper in search.results()]
    outs = list()
    for paper in search.results():
        try:
            outs.append(return_out.remote(paper))
        except:
            pass
    # store in df
    dfdata = pd.DataFrame(ray.get(outs), columns = ['short_id', 'publised_dt'])
    # end time counter and estimate diference
    toc = datetime.now()
    tictoc = ((toc-tic).seconds)/60. # minutes
    # display
    print(f"[info] Process time spent {tictoc} minutes")
    # save output
    path_output = os.path.join(folder_output, f'table-id_papers-{cat}.csv')
    dfdata.to_csv(path_output, index = False)
    print(f"[info] It was save {dfdata.shape[0]} records.")
    # shutdown ray
    ray.shutdown()


# end principal time counter and estimate diference
toc_p = datetime.now()
tictoc_p = ((toc_p-tic_p).seconds)/60. # minutes
# end
quit('done!')




