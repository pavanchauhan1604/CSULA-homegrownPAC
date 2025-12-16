import os
import sys
import time

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import requests
from bs4 import BeautifulSoup
import requests.exceptions

from src.data_management.data_import import get_all_sites_domain_names

# all_site_list =[
#     "aac.sfsu.edu",
#     "aapi.sfsu.edu",
#     "aas.sfsu.edu",
#     "academic.sfsu.edu",
#     "academicresources.sfsu.edu",
#     "access.sfsu.edu",
#     "accessalert.sfsu.edu",
#     "act.sfsu.edu",
#     "activities.sfsu.edu",
#     "advservices.sfsu.edu",
#     "advising.sfsu.edu",
#     "advisinghub.sfsu.edu",
#     "advisinglca.sfsu.edu",
#     "affordablelearning.sfsu.edu",
#     "africana.sfsu.edu",
#     "alumni.sfsu.edu",
#     "amed.sfsu.edu",
#     "anthropology.sfsu.edu",
#     "apiabiography.sfsu.edu",
#     "at.sfsu.edu",
#     "autism.sfsu.edu",
#     "basicneeds.sfsu.edu",
#     "budget.sfsu.edu",
#     "bursar.sfsu.edu",
#     "businessjapanese.sfsu.edu",
#     "cad.sfsu.edu",
#     "campusmemo.sfsu.edu",
#     "campusrec.sfsu.edu",
#     "careergrad.sfsu.edu",
#     "childrenscampus.sfsu.edu",
#     "chss.sfsu.edu",
#     "cj.sfsu.edu",
#     "classics.sfsu.edu",
#     "climate.sfsu.edu",
#     "cls.sfsu.edu",
#     "commencement.sfsu.edu",
#     "commons.sfsu.edu",
#     "communicationstudies.sfsu.edu",
#     "conduct.sfsu.edu",
#     "counseling.sfsu.edu",
#     "cpdc.sfsu.edu",
#     "cregs.sfsu.edu",
#     "cs.sfsu.edu",
#     "csme.sfsu.edu",
#     "csugis.sfsu.edu",
#     "campussafety.sfsu.edu",
#     "design.sfsu.edu",
#     "develop.sfsu.edu",
#     "gatorsmartstart.sfsu.edu",
#     "docfilm.sfsu.edu",
#     "docusign.sfsu.edu",
#     "dos.sfsu.edu",
#     "undocugators.sfsu.edu",
#     "tornado.sfsu.edu",
#     "ecse.sfsu.edu",
#     "edd.sfsu.edu",
#     "edelman.sfsu.edu",
#     "eed.sfsu.edu",
#     "ehs.sfsu.edu",
#     "elsit.sfsu.edu",
#     "em.sfsu.edu",
#     "engineering.sfsu.edu",
#     "eop.sfsu.edu",
#     "equity.sfsu.edu",
#     "erm.sfsu.edu",
#     "esn.sfsu.edu",
#     "ethnicstudies.sfsu.edu",
#     "facaffairs.sfsu.edu",
#     "facilities.sfsu.edu",
#     "familyproject.sfsu.edu",
#     "www.foundation.sfsu.edu",
#     "fellowships.sfsu.edu",
#     "cfsd.sfsu.edu",
#     "financialaid.sfsu.edu",
#     "flagship.sfsu.edu",
#     "future.sfsu.edu",
#     "gallery.sfsu.edu",
#     "gatorgreats.sfsu.edu",
#     "you.sfsu.edu",
#     "coe.sfsu.edu",
#     "geog.sfsu.edu",
#     "gis.sfsu.edu",
#     "globalclassroom.sfsu.edu",
#     "govrel.sfsu.edu",
#     "grad.sfsu.edu",
#     "graymatterlab.sfsu.edu",
#     "gsp.sfsu.edu",
#     "hackathon.sfsu.edu",
#     "health.sfsu.edu",
#     "healthequity.sfsu.edu",
#     "history.sfsu.edu",
#     "home.sfsu.edu",
#     "housing.sfsu.edu",
#     "hr.sfsu.edu",
#     "ia.sfsu.edu",
#     "iac.sfsu.edu",
#     "ibhequity.sfsu.edu",
#     "icce.sfsu.edu",
#     "instructionalcontinuity.sfsu.edu",
#     "investiture.sfsu.edu",
#     "ir.sfsu.edu",
#     "jewish.sfsu.edu",
#     "journalism.sfsu.edu",
#     "kin.sfsu.edu",
#     "ltns.sfsu.edu",
#     "liberalstudies.sfsu.edu",
#     "longmore.sfsu.edu",
#     "maethnicstudies.sfsu.edu",
#     "magazine.sfsu.edu",
#     "maps.sfsu.edu",
#     "math.sfsu.edu",
#     "meis.sfsu.edu",
#     "metro.sfsu.edu",
#     "mobility.sfsu.edu",
#     "morrison.sfsu.edu",
#     "museumstudies.sfsu.edu",
#     "www.musicdance.sfsu.edu",
#     "mystory.sfsu.edu",
#     "nagpra.sfsu.edu",
#     "navigator.sfsu.edu",
#     "news.sfsu.edu",
#     "www.nursing.sfsu.edu",
#     "oes.sfsu.edu",
#     "oip.sfsu.edu",
#     "olli.sfsu.edu",
#     "recruitment.sfsu.edu",
#     "pace.sfsu.edu",
#     "parking.sfsu.edu",
#     "pays.sfsu.edu",
#     "pbk.sfsu.edu",
#     "philosophy.sfsu.edu",
#     "physics.sfsu.edu",
#     "plan.sfsu.edu",
#     "planning.sfsu.edu",
#     "poetry.sfsu.edu",
#     "politicalscience.sfsu.edu",
#     "president.sfsu.edu",
#     "procurement.sfsu.edu",
#     "psm.sfsu.edu",
#     "psychology.sfsu.edu",
#     "caps.sfsu.edu",
#     "pt.sfsu.edu",
#     "publichealth.sfsu.edu",
#     "qaservices.sfsu.edu",
#     "queercinemaproject.sfsu.edu",
#     "research.sfsu.edu",
#     "reslife.sfsu.edu",
#     "retire.sfsu.edu",
#     "rfsa.sfsu.edu",
#     "rivers.sfsu.edu",
#     "recdept.sfsu.edu",
#     "rrs.sfsu.edu",
#     "safezone.sfsu.edu",
#     "westernnoyce.sfsu.edu",
#     "convocation.sfsu.edu",
#     "seo.sfsu.edu",
#     "sete.sfsu.edu",
#     "sfamp.sfsu.edu",
#     "sfbaynerr.sfsu.edu",
#     "reclaimingnature.sfsu.edu",
#     "sfsuais.sfsu.edu",
#     "sierra.sfsu.edu",
#     "slhs.sfsu.edu",
#     "socwork.sfsu.edu",
#     "sped.sfsu.edu",
#     "sss.sfsu.edu",
#     "studentsuccess.sfsu.edu",
#     "sustain.sfsu.edu",
#     "techgovernance.sfsu.edu",
#     "titleix.sfsu.edu",
#     "transfer.sfsu.edu",
#     "transforms.sfsu.edu",
#     "tutoring.sfsu.edu",
#     "tviomfriends.sfsu.edu",
#     "ucorp.sfsu.edu",
#     "univpark.sfsu.edu",
#     "upd.sfsu.edu",
#     "uwa.sfsu.edu",
#     "veterans.sfsu.edu",
#     "viprogram.sfsu.edu",
#     "vpsaem.sfsu.edu",
#     "cease.sfsu.edu",
#     "wgsdept.sfsu.edu",
#     "businessanalytics.sfsu.edu",
#     "msa.sfsu.edu",
#     "erp.sfsu.edu",
#     "sustainablemba.sfsu.edu",
#     "execed.sfsu.edu",
#     "marketing.sfsu.edu",
#     "management.sfsu.edu",
#     "mba.sfsu.edu",
#     "finance.sfsu.edu",
#     "ds.sfsu.edu",
#     "labor-studies.sfsu.edu",
#     "nicemba.sfsu.edu",
#     "vista.sfsu.edu",
#     "accounting.sfsu.edu",
#     "vista-room.sfsu.edu",
#     "biotechmba.sfsu.edu",
#     "gbp.sfsu.edu",
#     "economics.sfsu.edu",
#     "ibus.sfsu.edu",
#     "htm.sfsu.edu",
#     "vistaroom.sfsu.edu",
#     "emba.sfsu.edu",
#     "cob.sfsu.edu",
#     "is.sfsu.edu",
#     "itsecurity.sfsu.edu",
#     "itpolicy.sfsu.edu",
#     "adminfin.sfsu.edu",
#     "policiesandpracticedirectives.sfsu.edu",
#     "advance.sfsu.edu",
#     "www.art.sfsu.edu",
#     "art.sfsu.edu",
#     "martinwong.sfsu.edu",
#     "www.beca.sfsu.edu",
#     "ksfs.sfsu.edu",
#     "tvcenter.sfsu.edu",
#     "biology.sfsu.edu",
#     "beca.sfsu.edu",
#     "biology.sfsu.edu",
#     "climatehq.sfsu.edu",
#     "busops.sfsu.edu",
#     "riskandsafetyservices.sfsu.edu",
#     "ctfd.sfsu.edu",
#     "qlt.sfsu.edu",
#     "qolt.sfsu.edu",
#     "wac.sfsu.edu",
#     "ceetl.sfsu.edu",
#     "cpage.sfsu.edu",
#     "prehealth.sfsu.edu",
#     "sfsummer.sfsu.edu",
#     "ali.sfsu.edu",
#     "www.cpage.sfsu.edu",
#     "www.cel.sfsu.edu",
#     "cel.sfsu.edu",
#     "meetings.sfsu.edu",
#     "ces.sfsu.edu",
#     "summerconf.sfsu.edu",
#     "biochemistry.sfsu.edu",
#     "chembiochem.sfsu.edu",
#     "chemistry.sfsu.edu",
#     "cinema.sfsu.edu",
#     "humcwl.sfsu.edu",
#     "complit.sfsu.edu",
#     "afm.sfsu.edu",
#     "gtac.sfsu.edu",
#     "cose.sfsu.edu",
#     "pinc.sfsu.edu",
#     "cssc.sfsu.edu",
#     "emfimage.sfsu.edu",
#     "catalyze.sfsu.edu",
#     "merl.sfsu.edu",
#     "creativewriting.sfsu.edu",
#     "greenhouse.sfsu.edu",
#     "csld.sfsu.edu",
#     "career.sfsu.edu",
#     "careerservices.sfsu.edu",
#     "sfcall.sfsu.edu",
#     "bold.thinking.sfsu.edu",
#     "developmentalstudies.sfsu.edu",
#     "www.docfilm.sfsu.edu",
#     "drc.sfsu.edu",
#     "earth.sfsu.edu",
#     "tpw.sfsu.edu",
#     "matesol.sfsu.edu",
#     "english.sfsu.edu",
#     "linguistics.sfsu.edu",
#     "cmls.sfsu.edu",
#     "etc.sfsu.edu",
#     "rtc.sfsu.edu",
#     "eoscenter.sfsu.edu",
#     "riptides.sfsu.edu",
#     "eos.sfsu.edu",
#     "imes.sfsu.edu",
#     "marineops.sfsu.edu",
#     "safety.sfsu.edu",
#     "sfstatefacilities.sfsu.edu",
#     "foundation.sfsu.edu",
#     "sfsufdn.sfsu.edu",
#     "tax.sfsu.edu",
#     "financialservices.sfsu.edu",
#     "fiscaff.sfsu.edu",
#     "www.flagship.sfsu.edu",
#     "hotshots.sfsu.edu",
#     "mentalhealthcheckup.sfsu.edu",
#     "gatorhealth.sfsu.edu",
#     "righttoknow.sfsu.edu",
#     "humanities.sfsu.edu",
#     "americanstudies.sfsu.edu",
#     "humanitiesliberalstudies.sfsu.edu",
#     "latinamericanstudies.sfsu.edu",
#     "southasianstudies.sfsu.edu",
#     "internationalrelations.sfsu.edu",
#     "irgrad.sfsu.edu",
#     "cids.sfsu.edu",
#     "ids.sfsu.edu",
#     "askhr.sfsu.edu",
#     "doit.sfsu.edu",
#     "tech.sfsu.edu",
#     "its.sfsu.edu",
#     "drupal.sfsu.edu",
#     "latino.sfsu.edu",
#     "lca.sfsu.edu",
#     "artshumanities.sfsu.edu",
#     "ica.sfsu.edu",
#     "arts.sfsu.edu",
#     "cats.sfsu.edu",
#     "www.creativearts.sfsu.edu",
#     "creativestate.sfsu.edu",
#     "library.sfsu.edu",
#     "longmoreinstitute.sfsu.edu",
#     "puboff.sfsu.edu",
#     "marcomm.sfsu.edu",
#     "logo.sfsu.edu",
#     "www.persian.sfsu.edu",
#     "japanese.sfsu.edu",
#     "persian.sfsu.edu",
#     "chinese.sfsu.edu",
#     "italian.sfsu.edu",
#     "mllab.sfsu.edu",
#     "mll.sfsu.edu",
#     "french.sfsu.edu",
#     "spanish.sfsu.edu",
#     "german.sfsu.edu",
#     "fllab.sfsu.edu",
#     "russian.sfsu.edu",
#     "foreign.sfsu.edu",
#     "museum.sfsu.edu",
#     "musicdance.sfsu.edu",
#     "music.sfsu.edu",
#     "newstudentprograms.sfsu.edu",
#     "newstudentguide.sfsu.edu",
#     "nursing.sfsu.edu",
#     "studyabroad.sfsu.edu",
#     "onecard.sfsu.edu",
#     "onecardonline.sfsu.edu",
#     "baypass.sfsu.edu",
#     "outreach.sfsu.edu",
#     "www.physics.sfsu.edu",
#     "president-search.sfsu.edu",
#     "developmentalpsych.sfsu.edu",
#     "psyservs.sfsu.edu",
#     "www.pt.sfsu.edu",
#     "queercinemainstitute.sfsu.edu",
#     "cms.sfsu.edu",
#     "registrar.sfsu.edu",
#     "www.registrar.sfsu.edu",
#     "testing.sfsu.edu",
#     "efh.sfsu.edu",
#     "rpt.sfsu.edu",
#     "secondaryed.sfsu.edu",
#     "senate.sfsu.edu",
#     "sfbuild.sfsu.edu",
#     "sxs.sfsu.edu",
#     "sociology.sfsu.edu",
#     "socsxs.sfsu.edu",
#     "comdis.sfsu.edu",
#     "theatredance.sfsu.edu",
#     "theatre.sfsu.edu",
#     "www.theatre.sfsu.edu",
#     "ueap.sfsu.edu",
#     "lac.sfsu.edu",
#     "carp.sfsu.edu",
#     "exco.sfsu.edu",
#     "ugs.sfsu.edu",
#     "wasc.sfsu.edu",
#     "universityenterprises.sfsu.edu",
#     "realestate.sfsu.edu",
#     "red.sfsu.edu",
#     "ue.sfsu.edu",
#     "efh.sfsu.edu",
#     "aspire.sfsu.edu",
#     "fina.sfsu.edu",
#     "gcoe.sfsu.edu",
#     "wellness.sfsu.edu",
#     "air.sfsu.edu",
#
# ]

import os
import time
import requests
import re
from bs4 import BeautifulSoup
from scrapy.linkextractors import LinkExtractor
from pydispatch import dispatcher
from scrapy import signals
from datetime import datetime

##############################
# Make sure the following function exists somewhere:
# def get_all_sites_domain_names():
#     return [...]
##############################

spider_template = """
# -*- coding: utf-8 -*-
import os
    
import scrapy
import re
from scrapy.linkextractors import LinkExtractor
from pydispatch import dispatcher
from scrapy import signals
from datetime import datetime

from ..box_handler import get_box_contents


class {class_name}(scrapy.Spider):
    name = '{name}'
    start_urls = ['https://{site_url}']
    output_folder = r'C:\\Users\\913678186\\Box\\ATI\\PDF Accessibility\\SF State Website PDF Scans\\{save_folder}'

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super({class_name}, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def __init__(self):
        super().__init__()
        self.matched_links = []  # Store matched links, if needed
        self.pdf_links = []      # Store PDF links as tuples (pdf_url, referrer_url)
        self.failed_box_links = []  # Store Box links that failed to resolve

    def parse(self, response):
        \"\"\"
        Extracts all <a href="..."> links from the page and decides:
          - If the link is within {site_url}, follow it or store if it's a PDF.
          - If the link is a Box.com link, hand it off to parse_box_link.
        \"\"\"

        # Regex for {site_url} domain (handles both http and https)
        access_url_pattern = re.compile(r'https?://{site_url}/.*', re.IGNORECASE)

        # Regex for box.com links
        box_url_pattern = re.compile(r'https?://sfsu\\.box\\.com/s/.*', re.IGNORECASE)

        # Regex to detect .pdf files
        pdf_pattern = re.compile(r'.*\\.pdf$', re.IGNORECASE)

        # Extract all <a href="..."> attributes
        extracted_links = response.css('a::attr(href)').getall()

        for link in extracted_links:
            absolute_url = response.urljoin(link)

            # If the link is internal to {site_url}
            if access_url_pattern.match(absolute_url):
                # Check if it’s a PDF
                if pdf_pattern.match(absolute_url):
                    self.pdf_links.append((absolute_url, response.url))
                else:
                    yield response.follow(absolute_url, self.parse)

            # Otherwise, if it’s a Box.com link
            elif box_url_pattern.match(absolute_url):
                history = response.meta.get('history', [])
                history.append(response.url)
                yield response.follow(absolute_url, self.parse_box_link, meta={{'history': history}})

    def parse_box_link(self, response):
        \"\"\"
        A custom handler for Box.com links. 
        get_box_contents(url) should return a tuple of (bool, pdf_url),
        where bool indicates if a PDF was found.
        \"\"\"
        pdf_url = get_box_contents(response.url)
        referring_page = response.meta.get('history', [None])[0]

        if pdf_url and pdf_url[0]:
            self.pdf_links.append((pdf_url[1], referring_page))
        else:
            # If no PDF was found, record this Box link as "failed" for reference
            self.failed_box_links.append((pdf_url[1] if pdf_url else response.url, referring_page))

        self.logger.info('Handling a Box.com link: %s', response.url)

    def spider_closed(self, spider):
        \"\"\"
        Called automatically when the spider finishes.
        Ensures the output folder exists, then writes discovered PDF links
        (and their referring URL) to scanned_pdfs.txt with a timestamp.
        \"\"\"
        os.makedirs(self.output_folder, exist_ok=True)
        output_file_path = os.path.join(self.output_folder, 'scanned_pdfs.txt')
        failed_box_path = os.path.join(self.output_folder, 'failed_box_links.txt')

        with open(output_file_path, 'w', encoding='utf-8') as file:
            for pdf_link, ref_url in self.pdf_links:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                file.write(f"{{pdf_link}} {{ref_url}} {{timestamp}}\\n")
                
                
        with open(failed_box_path, 'w', encoding='utf-8') as file:
            for pdf_link, ref_url in self.failed_box_links:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                file.write(f"{{pdf_link}} {{ref_url}} {{timestamp}}\\n")

        self.logger.info("PDF LINKS saved to %s", output_file_path)
"""

output_dir = "sf_state_pdf_scan/sf_state_pdf_scan/spiders"
os.makedirs(output_dir, exist_ok=True)

all_sites = get_all_sites_domain_names()

# Dictionary to track counts for each base site name
site_name_counts = {}

failed = []

for site in all_sites:
    time.sleep(0.1)
    try:
        response = requests.get("https://" + site)
    except (requests.exceptions.SSLError, requests.exceptions.ConnectionError):
        failed.append(site)
        continue

    soup = BeautifulSoup(response.content, 'html.parser')

    site_name_tag = soup.find('span', class_='site-name')
    if site_name_tag and site_name_tag.find('a'):
        base_site_name = site_name_tag.find('a').text.strip()
    else:
        base_site_name = 'SiteNameNotFound'

    # Get the current count for this base site name and update it
    count = site_name_counts.get(base_site_name, 0)
    if count > 0:
        unique_site_name = f"{base_site_name}{count}"
    else:
        unique_site_name = base_site_name
    site_name_counts[base_site_name] = count + 1

    # Use unique_site_name for further processing

    # Clean the unique site name for the class name (e.g. "My Site" -> "MySiteSpider")
    site_name_cleaned_for_class = ''.join(
        word.capitalize()
        for word in ''.join(e if e.isalnum() or e.isspace() else ' ' for e in unique_site_name).split()
    )

    # Clean for the spider name, removing non-alphanumeric but allowing spaces
    site_name_cleaned_for_name = ''.join(
        e if e.isalnum() or e.isspace() else ''
        for e in unique_site_name
    )

    # Clean for the file title (replace spaces with underscores)
    site_name_cleaned_for_file_title = ''.join(
        e if e.isalnum() or e.isspace() else ''
        for e in unique_site_name
    ).replace(' ', '_')

    save_folder = site.replace('.', '-').lower()

    class_name = f"{site_name_cleaned_for_class}Spider"

    spider_code = spider_template.format(
        class_name=class_name,
        name=f"{site_name_cleaned_for_name.lower().replace(' ', '_')}_spider",
        site_url=site,
        spider_name=site_name_cleaned_for_name.lower(),  # extra arg, not used in template, but no harm
        save_folder=save_folder
    )

    file_path = os.path.join(output_dir, f"{site_name_cleaned_for_file_title.lower()}_spider.py")
    with open(file_path, 'w', encoding="utf-8") as file:
        file.write(spider_code)

    print(f"Generated spider for {site}: {file_path}")

print(f"Failed sites: {failed}")