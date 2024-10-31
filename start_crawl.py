from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import sys

settings = get_project_settings()

folder = sys.argv[1]
domains = sys.argv[2].split(',')
start_pages = sys.argv[3].split(',')

print(f'folder: {folder}')
print(f'domains: {domains}')
print(f'start_pages: {start_pages}')

settings['JOBDIR'] = f'./jobs/{folder}/'
process = CrawlerProcess(settings)

# 'followall' is the name of one of the spiders of the project.
process.crawl("quotes", domains=domains, start_pages=start_pages)
process.start()  # the script will block here until the crawling is finished
