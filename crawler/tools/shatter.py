import gzip
import io

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from crawler.model.crawl_result import CrawlResult
from crawler.model.shatter_result import ShatterResult

from lxml import etree, html
from lxml.html import HtmlElement
from io import StringIO

import gc

engine = create_engine("mysql+pymysql://scrapy:12345@localhost/crawler?charset=utf8mb4")

STOP_TAGS = set(['head', 'script', 'noscript'])
FLATTEN_TAG = set(['br', 'p', 'ul', 'li', 'span', 'em', 'strong', 'a', 'h1', 'h2', 'h3', 'h4', 'h5'])

DOMAIN = 'www.theguardian.com'

class StringBuilder:
    data = None

    def __init__(self):
        self.data = StringIO()

    def append(self, tail):
        self.data.write(tail)

    def __str__(self):
        return self.data.getvalue()

Session = sessionmaker(bind=engine)
def save_shatter_result(r):
    session = Session()
    session.add(r)
    session.commit()
    session.close()

def process_node(node, crawl_id, current_path='', text_stack=[]):
    if type(node) is not HtmlElement:
        return
    if node.tag in STOP_TAGS:
        return

    r = ShatterResult(domain=DOMAIN, crawl_id=crawl_id)
    parent_xpath = current_path
    # Generate the current XPath
    if node.tag != 'html' and node.tag != 'body' and 'class' in node.attrib:
        c = node.attrib['class']
        current_xpath = f"{current_path}/{node.tag}#{c}"
    else:
        current_xpath = f"{current_path}/{node.tag}"

    root = False
    if len(text_stack) == 0:
        root = True

    r.xpath = current_xpath
    if node.tag not in FLATTEN_TAG:
        text_stack.append(StringBuilder())

    text = node.text
    if text is not None:
        text = text.strip(' \n\t')

    if node.tag == 'a':
        text = '{Anchor}'

    if text is not None and len(text) > 0:
        for builder in text_stack:
            builder.append(text)

    # Print the current XPath
    #if node.tag not in FLATTEN_TAG:
    #    print(current_xpath)

    # Iterate through child nodes
    for index, child in enumerate(node):
        if node.tag in FLATTEN_TAG:
            process_node(child, crawl_id, parent_xpath, text_stack)
        else:
            process_node(child, crawl_id, current_xpath, text_stack)

    if node.tag not in FLATTEN_TAG:
        r.text = str(text_stack[-1])
        a = len(text_stack)
        text_stack.pop()
        save_shatter_result(r)


def main():
    while True:
        session = Session()
        crawl_result = session.query(CrawlResult).filter(
            CrawlResult.domain == DOMAIN,
            CrawlResult.shattered == False
        ).first()

        if crawl_result is None:
            print('All entries are done')
            return

        print(f'Working on {crawl_result.id} {crawl_result.url}')
        try:
            if crawl_result.content_encoding == 'gzip':
                tree = html.fromstring(crawl_result.decompressed_content)
            else:
                tree = html.fromstring(crawl_result.content.decode('utf-8'))

            process_node(tree, crawl_result.id)
            tree.clear()
        except Exception as e:
            print(f'Failed to process: {e}')
        finally:
            crawl_result.shattered = True
            session.commit()
            session.close()

if __name__ == '__main__':
    main()

