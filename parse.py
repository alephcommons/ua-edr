from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse
from zipfile import ZipFile
from lxml import etree
from pprint import pprint
from typing import IO, BinaryIO, Dict, Optional, Set
from lxml.etree import _Element as Element, tostring
from numpy import short
from zavod import Zavod, init_context
from followthemoney.proxy import EntityProxy
from followthemoney.util import join_text
from followthemoney.util import make_entity_id


def tag_text(el: Element) -> str:
    return tostring(el, encoding="utf-8").decode("utf-8")


def parse_uo(context: Zavod, fh: IO[bytes]):
    for idx, (_, el) in enumerate(etree.iterparse(fh, tag="RECORD")):
        if idx > 0 and idx % 10000 == 0:
            context.log.info("Parse UO records: %d..." % idx)
        # print(tag_text(el))

        company = context.make("Company")
        long_name = el.findtext("./NAME")
        short_name = el.findtext("./SHORT_NAME")
        edrpou = el.findtext("./EDRPOU")
        if short_name and len(short_name.strip()):
            company.add("name", short_name)
            company.add("alias", long_name)
        else:
            company.add("name", long_name)

        unique_id = make_entity_id(edrpou, short_name, long_name)
        company.id = context.make_slug(edrpou, unique_id, strict=False)
        if company.id is None:
            context.log.warn("Could not generate company ID", xml=tag_text(el))
            continue
        company.add("registrationNumber", edrpou)
        company.add("jurisdiction", "ua")
        company.add("address", el.findtext("./ADDRESS"))
        company.add("classification", el.findtext("./KVED"))
        company.add("status", el.findtext("./STAN"))
        context.emit(company)

        for boss in el.findall(".//BOSS"):
            name = boss.text
            if name is None:
                continue
            director = context.make("Person")
            director.id = context.make_id(unique_id, name)
            director.add("name", name)
            context.emit(director)

            directorship = context.make("Directorship")
            directorship.id = context.make_id(unique_id, "BOSS", name)
            directorship.add("organization", company)
            directorship.add("director", director)
            context.emit(director)

        # TODO: beneficiary
        # TODO: founder
        el.clear()


# def parse_fop(context: Zavod, fh: BinaryIO):
#     for idx, (_, el) in enumerate(etree.iterparse(fh, tag="RECORD")):
#         if idx > 0 and idx % 10000 == 0:
#             context.log.info("Parse FOP records: %d..." % idx)
#         print(tag_text(el))
#         el.clear()


def crawl(context: Zavod, url: str):
    path = context.fetch_resource("data.zip", url)
    context.log.info("Parsing: %s" % path)
    with ZipFile(path, "r") as zip:
        for name in zip.namelist():
            if not name.lower().endswith(".xml"):
                continue
            with zip.open(name, "r") as fh:
                if "EDR_UO" in name:
                    parse_uo(context, fh)
                # if "EDR_FOP" in name:
                #     parse_fop(context, fh)


if __name__ == "__main__":
    with init_context("ua_edr", "ua-edr") as context:
        crawl(context, "https://data.opensanctions.org/contrib/ua_edr/23022022.zip")
