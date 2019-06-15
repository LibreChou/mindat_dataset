import numpy as np
import pandas as pd
from queue import Queue
from threading import Thread
from time import time
import os
import requests
from pathlib import Path
from queue import Queue


mineral_names_df = pd.read_csv('data/mineral_id_to_name.csv', index_col='mineral_id').drop('Unnamed: 0', 1)
images_df = pd.read_csv('data/image_general.csv', index_col='image_id').drop('Unnamed: 0', 1)
image_minerals_df = pd.read_csv('data/image_mineral_lists.csv', index_col='image_id').drop('Unnamed: 0', 1)

def download_image(img_id, img_file, dest='.'):
    dest = Path(dest)
    save_file = dest/img_file.replace('/', '_')
    if save_file.exists():
        return
    #os.makedirs(dest, exist_ok=True)
    headers = {'referer' : 'https://www.mindat.org/photo-{}.html'.format(img_id)}
    req = requests.get('https://www.mindat.org/imagecache/' + img_file, headers=headers)
    if req.status_code != 200:
        print(img_id, req)
        return
    with open(str(save_file), 'wb') as file:
        file.write(req.content)
        
        
download_queue = Queue(50)
def worker():
    while True:
        img_id, img_file, dest = download_queue.get()
        download_image(img_id, img_file, dest)
        download_queue.task_done()
    
for i in range(50):
    t = Thread(target=worker)
    t.daemon = True
    t.start()
  
def download_threading(df, dest='train'):
    dest = Path(dest)
    os.makedirs(str(dest), exist_ok=True)
    N = len(df)
    for row in df.iterrows():
        img_id, row = row
        img_file = row.image_file
        download_queue.put((img_id, img_file, dest))

t0 = time()
download_threading(images_df, dest='images')
print(time() - t0)