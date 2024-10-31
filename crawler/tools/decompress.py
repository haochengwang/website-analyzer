import gzip
import io

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from crawler.model.crawl_result import CrawlResult

engine = create_engine("mysql+pymysql://scrapy:12345@localhost/crawler?charset=utf8mb4")
def main():
    while True:
        Session = sessionmaker(bind=engine)
        session = Session()
        crawl_result = session.query(CrawlResult).filter(
            CrawlResult.domain == 'blog.samaltman.com',
            CrawlResult.decompressed_content_filled == True,
            CrawlResult.content_encoding == 'gzip',
        ).first()

        if crawl_result is None:
            print('All entries are decompressed')
            return

        print(f'Working on {crawl_result.id} {crawl_result.url}')
        buf = io.BytesIO(crawl_result.content)
        with gzip.GzipFile(fileobj=buf) as gz:
            decompressed_bytes = gz.read()

        encodings = ['utf-8', 'ascii', 'latin-1']
        for encoding in encodings:
            try:
                crawl_result.decompressed_content = decompressed_bytes.decode(encoding)
                break
            except UnicodeDecodeError as e:
                pass
        session.commit()
        session.close()

if __name__ == '__main__':
    main()

