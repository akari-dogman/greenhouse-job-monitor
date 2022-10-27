import requests
import os
from bs4 import BeautifulSoup
import database
from datetime import datetime
from loguru import logger

def parse_webpage_extract_departments(http_text):
    eph_departments = {}
    soup = BeautifulSoup(http_text, 'html.parser')
    soup_departments = soup.find_all('section', {'class': 'level-0'})
    for department in soup_departments:
        tag = department.find('h2')
        eph_departments[tag['id']] = tag.text
    return eph_departments

def parse_webpage_extract_jobs(http_text):
    eph_jobs = {}
    soup = BeautifulSoup(http_text, 'html.parser')
    soup_jobs = soup.find_all('div', {'class': 'opening'})
    for job in soup_jobs:
        name = job.find('a')
        job_id = name['href'].split('/')[-1]
        location = job.find('span',{'class': 'location'})
        job_obj = {
            'name':name.text,
            'location':location.text,
            'job_id':int(job_id),
            'department_id':int(job['department_id']),
            'office_id':int(job['office_id'])
        }
        eph_jobs[job_id] = job_obj
    return eph_jobs

def send_hook_on_job_found(job):
    department_name = list_of_departments[str(job['department_id'])]
    webhook_obj = {
        "content": f"New {slug} job found!",
        "embeds": [
            {
                "title": job['name'],
                "url": permalink_prepend + str(job['job_id']),
                "color": 4285283,
                "fields": [
                    {
                        "name": "Department",
                        "value": department_name,
                        "inline": True
                    },
                    {
                        "name": "Location",
                        "value":job['location'],
                        "inline": True
                    }
                ],
                "footer": {
                    "text": f"Job ID: {job['job_id']} | created by akari-dogman"
                },
                "timestamp" : str(datetime.now().isoformat())
            }
        ]
    }
    webhook_request = requests.post(discord_webhook,json=webhook_obj)
    print(webhook_request.status_code)
    pass

def get_webpage(url):
    ''' Takes in a URL, returns Request object '''
    headers = {
        'User-Agent': 'akari-dogman/Github greenhousechecker'
    }
    greenhouse_request = requests.get(url,headers=headers)
    if greenhouse_request.status_code != 200:
        raise Exception(f'HTTP error code raised {greenhouse_request.status_code} for URL {url}')
    return greenhouse_request

def init_check():
    global slug
    global discord_webhook
    global permalink_prepend
    slug = os.getenv('SLUG')
    discord_webhook = os.getenv('DISCORD_WEBHOOK')
    permalink_prepend = os.getenv('PL_PREPEND')
    if discord_webhook == None or slug == None:
        logger.error('One of the required environment labels is not set. Halting script... | DISCORD WEBHOOK: {} | SLUG: {}'.format(discord_webhook,slug))
        exit("ENVIRONMENT LABEL NOT SET")
    if permalink_prepend == None:
        permalink_prepend = 'https://boards.greenhouse.io/{}/jobs/'.format(slug)
    if database.check_table_existence(slug) == False:
        logger.info('Table {} does not exist, creating...'.format(slug))
        database.create_job_table(slug)
    

def main():
    init_check()
    logger.info('Fetching greenhouse URL for {}'.format(slug))
    x = get_webpage('https://boards.greenhouse.io/{}/'.format(slug))
    global list_of_departments
    list_of_jobs = parse_webpage_extract_jobs(x.text)
    list_of_departments = parse_webpage_extract_departments(x.text)
    logger.info('Jobs found: {}, Departments found: {}'.format(len(list_of_jobs),len(list_of_departments)))
    db_jobs = database.fetch_all_jobs(slug)
    if len(db_jobs) == 0:
        for job in list_of_jobs:
            database.enter_job(slug,list_of_jobs[job])
        logger.info('Entered initial batch of jobs into the database. See you next time!')
    else:
        comprehension = { str(list_of_jobs[x]['job_id']) for x in list_of_jobs }
        diff = comprehension.difference(db_jobs)
        if len(diff) == 0:
            logger.info('No new jobs found. Exiting...')
            exit()
        if len(diff) > 0:
            logger.info('{} new jobs found!'.format(len(diff)))
            for new_job in diff:
                print('new job ID: {}, name: {}'.format(new_job,list_of_jobs[str(new_job)]))
                send_hook_on_job_found(list_of_jobs[str(new_job)])
            logger.info('deleting prev jobs from DB...')
            database.clear_all_jobs(slug)
            logger.info('entering new jobs...')
            for job in list_of_jobs:
                database.enter_job(slug,list_of_jobs[job])
            logger.info('done! see you next time')
            quit()

main()