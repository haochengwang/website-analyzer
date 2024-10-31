from mrjob.job import MRJob
from mrjob.step import MRStep

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from crawler.model.crawl_result import CrawlResult

from lxml import etree, html
from lxml.html import HtmlElement

from io import StringIO

STOP_TAGS = set(['head', 'script', 'noscript'])
FLATTEN_TAG = set(['br', 'p', 'b', 'i', 'u', 'font', 'ul', 'ol', 'li', 'span', 'em', 'strong', 'a', 'pre', 'h1', 'h2', 'h3', 'h4', 'h5'])

DOMAIN = 'paulgraham.com'

class StringBuilder:
    data = None

    def __init__(self):
        self.data = StringIO()

    def append(self, tail):
        self.data.write(tail)

    def __str__(self):
        return self.data.getvalue()

class MRWebPageAnalyzeMR(MRJob):
    def steps(self):
        return [
            MRStep(mapper=self.mapper_input),
            MRStep(mapper=self.mapper_shatter_page,
                   reducer=self.reducer_count)]
        
    def mapper_input(self, _, entry):
        engine = create_engine("mysql+pymysql://scrapy:12345@localhost/crawler?charset=utf8mb4")
        Session = sessionmaker(bind=engine)
        session = Session()
        crawl_result = session.query(CrawlResult).filter(
            CrawlResult.domain == DOMAIN,
            CrawlResult.http_code == 200
        )

        for r in crawl_result:
            if r.decompressed_content is not None:
                self.increment_counter('shatter', 'db_entry_processed', 1)
                yield 1, {'content': r.decompressed_content}

        session.close()

    def mapper_shatter_page(self, _, entry):
        content = entry['content']
        try:
            tree = html.fromstring(content)
            for r in self.process_node(tree):
                yield r
        except Exception as e:
            self.increment_counter('shatter', 'exception', 1)
            self.increment_counter('shatter', f'exception-{e}', 1)

    def process_node(self, node, current_path = '', text_stack = []):
        if type(node) is not HtmlElement:
            return
        if node.tag in STOP_TAGS:
            return

        parent_xpath = current_path
        # Generate the current XPath
        if node.tag != 'html' and node.tag != 'body':
            if 'id' in node.attrib:
                nodeid = node.attrib['id']
                current_xpath = f'{current_path}/{node.tag}:{nodeid}'
            elif 'class' in node.attrib:
                nodeclass = node.attrib['class']
                current_xpath = f"{current_path}/{node.tag}#{nodeclass}"
            else:
                current_xpath = f"{current_path}/{node.tag}"
        else:
            current_xpath = f"{current_path}/{node.tag}"

        root = False
        if len(text_stack) == 0:
            root = True

        xpath = current_xpath
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

        # Iterate through child nodes
        for index, child in enumerate(node):
            if node.tag in FLATTEN_TAG:
                for r in self.process_node(child, parent_xpath, text_stack):
                    yield r
            else:
                for r in self.process_node(child, current_xpath, text_stack):
                    yield r

        self.increment_counter('shatter', 'xpath', 1)
        if node.tag not in FLATTEN_TAG:
            text = str(text_stack[-1])
            text_stack.pop()
            yield xpath, text
            self.increment_counter('shatter', 'xpath_shattered', 1)

    def reducer_count(self, xpath, text):
        text_dict = set(text)
        yield xpath, len(text_dict)

if __name__ == '__main__':
    MRWebPageAnalyzeMR.run()
