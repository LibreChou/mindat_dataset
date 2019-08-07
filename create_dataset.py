import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path
from PIL import Image
from time import time
import pandas as pd
import fire
import os
from queue import Queue
import argparse
from collections import defaultdict

def __main__(n_threads=5, start_idx=0, end_idx=100):
  print(n_threads)
  imgs_dict = {}
  specimens_images_dict = defaultdict(list)
  imgs_minerals_dict = {}
  imgs_comments_dict = {}
  location_names_dict = {}
  minerals_names_dict = {}
  url_queue = Queue(n_threads)

  def worker():
    while True:
      url = url_queue.get()
      try:
        page = requests.get(url, timeout=60)
      except:
        # if url is bad
        url_queue.task_done()
        continue
      soup = BeautifulSoup(page.content, 'html.parser')
      try:
        img_tag = soup.find(property='og:image')
        img_url = img_tag['content']
        spec_id = soup.find('div', {'class' : "minid_photo_page"}).a.text
        img_id = int(re.findall(r'(\d+)\.html', url)[0])
        if img_id%1000 == 0:
          print(img_id)
        img_file = re.findall(r'/(\w+/\w+/\w+\.\w+)', img_url)[0]
      except (TypeError, AttributeError) as e:
        #print(url, e)
        url_queue.task_done()
        continue
      except IndexError as e:
        print(url, e)
        url_queue.task_done()
        continue
      #url_queue.task_done()
      #continue
      '''
      get location name and id from location tag:
      <a href="loc-{location id}.html">{location name}</a>
      '''
      try:
        loc_tag = soup.find('div', id='titlebar').h2.div.a
        loc_name = loc_tag.text
        loc_url = loc_tag['href']
        loc_id = int(re.search(r'loc-(\d+)\.html', loc_url)[1])
        if not loc_id in location_names_dict:
          location_names_dict[loc_id] = loc_name
      except Exception as e:
        print(url, e)
        loc_id = None
      #get list of minerals in the image
      try: 
        title_tag = soup.find('div', id='titlebar').h2
        min_ids = []
        for tag in title_tag.find_all('a', href=re.compile(r'min-\d+\.html')):
          min_name = tag.text
          min_id = int(re.search(r'min-(\d+)\.html', tag['href'])[1])
          if not min_id in minerals_names_dict:
            minerals_names_dict[min_id] = min_name
          min_ids.append(min_id)
        imgs_minerals_dict[img_id] = min_ids
      except Exception as e:
        print(url, e)
      imgs_dict[img_id] = {'specimen_id' : spec_id, 'image_file' : img_file, 'location_id' : loc_id}
      specimens_images_dict[spec_id].append(img_id)
      imgs_comments_dict[img_id] = str(soup.find('div', {'class' : 'photocomments'}))
      url_queue.task_done()
      
  from threading import Thread
  for i in range(n_threads):
    t = Thread(target=worker)
    t.daemon = True
    t.start()
    
  t0 = time()
  for i in range(start_idx, end_idx):
    url_queue.put(f"https://www.mindat.org/photo-{i}.html")
  url_queue.join()
  print(time() - t0)
  
  os.makedirs('comments', exist_ok=True)
  for k, v in imgs_comments_dict.items():
    with open(f'comments/{k}.html', 'w') as file:
      file.write(v)
      
if __name__ == '__main__':
  fire.Fire(__main__)
  
  
