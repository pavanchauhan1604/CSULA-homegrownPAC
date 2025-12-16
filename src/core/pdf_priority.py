import json
import xml.etree.ElementTree as ET
import chardet
import pikepdf
from pdfminer import high_level
from pdfminer.layout import LTImage
import pdfminer
from pikepdf import Pdf, Dictionary, Array, String, Object, Name, PdfError, OutlineItem
import re
import hashlib

acrobat_ignore_profiles = {

    "5": ["1", "2"],
    "7.1": ["4", "6", "7"],
    "7.2": ["3", "10", "15", "16", "19", "26", "27", "28", "36", "37", "38", "39", "40", "41", "42", "43"],
    "7.9": ["1"],
    "7.10": ["2"],
    "7.15": ["1"],
    "7.18.1": ["1"],
    "7.18.2": ["1"],
    "7.18.3": ["1"],
    "7.18.4": ["2"],
    "7.18.6.2": ["1"],
    "7.18.8": ["1"],
    "7.20": ["1"],
    "7.21.3.1": ["1"],
    "7.21.3.2": ["1"],
    "7.21.3.3": ["1"],
    "7.21.4.1": ["2"],
    "7.21.4.2": ["1", "2"],


}

immediate_failures = {
    "7.1": ["3", "11"] # not tagged and likely image only

}


def find_ignore_profile(dict: dict):


    clause_id = dict.get("clause")
    test_number = dict.get("testNumber")

    if str(clause_id) in acrobat_ignore_profiles:
        if str(test_number) in acrobat_ignore_profiles[clause_id]:
            return True
    return False


def violation_counter(json_file):
    violations = {
        "violations": 0,
        "failed_checks": 0,
        "tagged": True,
        "check_for_image_only": False,
    }

    # First, detect the encoding of the file
    with open(json_file, 'rb') as rawdata:
        result = chardet.detect(rawdata.read())
        encoding = result['encoding']

    # Now, open the file with the detected encoding
    with open(json_file, 'r', encoding=encoding) as validation_file:
        try:
            validation = json.load(validation_file)
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {json_file}. File might be empty.")
            return violations

        # Handle case where validation might be a list or have different structure
        try:
            if isinstance(validation, list):
                # If it's a list, take the first item
                validation = validation[0] if validation else {}
            
            # validationResult is a list, get the first item
            validation_result = validation['report']['jobs'][0]['validationResult']
            if isinstance(validation_result, list):
                validation_result = validation_result[0] if validation_result else {}
            
            rule_summaries = validation_result['details']['ruleSummaries']
        except (KeyError, TypeError, IndexError) as e:
            # If the structure is not what we expect, return empty violations
            print(f"Warning: Unexpected VeraPDF JSON structure in {json_file}: {e}")
            return violations

        for rule in rule_summaries:

            if find_ignore_profile(dict(rule)):
                continue

            clause_id = rule.get("clause")
            test_number = rule.get("testNumber")

            if str(clause_id) in immediate_failures: ## hard coded
                if test_number == "11":  # not tagged
                    violations["tagged"] = False
                if test_number == "3":  # possibly image only
                    violations["check_for_image_only"] = True

            violations["violations"] += 1
            violations["failed_checks"] += rule["failedChecks"]

    return violations


def _get_page_number_of_page(page_obj: Object, document: Pdf):

    count = 0

    for each in list(document.Root.Pages.Kids):

        if each.get("/Type") == "/Pages":
            for page in each.get("/Kids"):
                count += 1
                if page == page_obj:
                    return count

        else:
            count += 1
            if each == page_obj:
                return count



def page_contains_text(page):
    if page.groups is None:
        return False
    for each in page.groups:
        if isinstance(each, pdfminer.layout.LTTextGroupLRTB):
            return True
    return False


def image_over_text(page):

    for item in list(page):

        if isinstance(item, pdfminer.layout.LTFigure):
            check = False
            for pdf_object in item._objs:
                if isinstance(pdf_object, LTImage):
                    check = True
                if check:
                    variance = ((item.x1 - item.x0) * (item.y1 - item.y0)) / ((page.x1 - page.x0) * (page.y1 - page.y0))
                    if 0.9 < variance < 1.1:  # Check to see if the size of the text image is the same as the page
                        return True
                    else:
                        continue
        continue
    return False


def check_status(document_location):
    pages = list(high_level.extract_pages(document_location))

    to_return = []
    for page in pages:

        image = image_over_text(page)
        text = page_contains_text(page)
        to_return.append((image,text))

    return to_return


def pdf_status(document_location):

    # True True = Image of text over text
    # False True = Text Only
    # True False = Only Image of Text
    # False False = No image of text and no page text

    t1 = 0
    t2 = 0
    page_stats = check_status(document_location)

    for each in page_stats:
        if each[0]:
            t1 += 1
        if each[1]:
            t2 += 1
    print(t1, t2)
    if t1 > 0 and t2 > 0:
        return "Image Over Text"  # Image of text over text
    if t1 == 0 and t2 != 0:
        return "Text Only"  # Text Only
    if t1 > 0 and t2 == 0:
        return "Image only"  # Only Image of Text
    if t1 == 0 and t2 == 0:
        return "No Image or Text"  # No image of text and no page text


def check_if_tagged(document):
    if isinstance(document, str):
        pdf = Pdf.open(document)
        if pdf.Root.get("/StructTreeRoot") is not None:
            return True
        else:
            return False
    if isinstance(document, Pdf):
        if document.Root.get("/StructTreeRoot") is not None:
            return True
        else:
            return False


def check_for_alt_tags(document):

    root = document.Root.get("/StructTreeRoot")
    roleMap = root.get("/RoleMap")
    document_photos = list()
    IDDict = {}

    if not check_if_tagged(document):
        raise Exception("PDF Not Tagged")

    MAX_DEPTH = 100  # maximum allowed recursion depth

    def recurse_s_node(node, depth=0):
        if depth > MAX_DEPTH:
            return

        def check_xObject():
            def check_xObject_image(iXobject):
                if iXobject.get("/Subtype") == "/Image":
                    image_bytes = iXobject.get_raw_stream_buffer()
                    hasher = hashlib.md5()
                    hasher.update(image_bytes)
                    image_hash = hasher.hexdigest()
                    derived_id = iXobject.get("/Height") + iXobject.get("/Width") + iXobject.get("/Length")
                    if "/Alt" in node.keys() and len(str(node.get('/Alt'))) > 0:
                        IDDict[image_hash] = True
                    else:
                        if derived_id in IDDict and IDDict[image_hash] is True:
                            IDDict[image_hash] = True
                        else:
                            IDDict[image_hash] = False

            try:
                resources = node.get('/Pg').get("/Resources")
                if "/XObject" in resources.keys():
                    XObject = resources.get("/XObject")
                    for key in XObject.keys():
                        if re.match(re.compile(r"/Fm\d|/P\d"), key):  # form XObject?
                            fxobject_resources = XObject[key].get("/Resources")
                            if "/XObject" in fxobject_resources.keys():
                                for xobject_key in fxobject_resources["/XObject"]:
                                    if re.match(re.compile(r"/Im\d"), xobject_key):  # image XObject?
                                        check_xObject_image(fxobject_resources["/XObject"][xobject_key])
                        else:
                            check_xObject_image(XObject[key])
            except AttributeError:
                print(repr(node.get('/Pg')))

        # Retrieve the /S value and handle list types
        s_value = node.get('/S')
        if isinstance(s_value, list) and len(s_value) > 0:
            s_value = s_value[0]
        if not isinstance(s_value, (str, pikepdf.Name)):
            return

        # Safe lookup in roleMap
        if roleMap is not None and hasattr(roleMap, 'keys') and len(roleMap.keys()) > 0:
            try:
                if roleMap.get(s_value) == Name("/Figure"):
                    check_xObject()
            except KeyError:
                if s_value == Name("/Figure"):
                    check_xObject()
        else:
            if s_value == Name("/Figure"):
                check_xObject()

    def recurse_k_nodes(node, depth=0):
        if depth > MAX_DEPTH:
            return

        if isinstance(node, Dictionary):
            if "/K" in node.keys():
                # Recurse on the /K entry (it may be a single object or a collection)
                recurse_k_nodes(node.get('/K'), depth + 1)
            if "/S" in node.keys():
                recurse_s_node(node, depth + 1)
        elif isinstance(node, Array):
            for each in node:
                if isinstance(each, Dictionary):
                    if "/K" in each.keys():
                        recurse_k_nodes(each.get("/K"), depth + 1)
                    if "/S" in each.keys():
                        recurse_s_node(each, depth + 1)
                elif isinstance(each, Array):
                    recurse_k_nodes(each, depth + 1)

    # Start the recursion from the root, with depth=0.
    recurse_k_nodes(root, 0)

    for figure in IDDict:
        document_photos.append(IDDict[figure])
    return document_photos


def verify_headings(document):

    root = document.Root.get("/StructTreeRoot")

    headings = []

    headings_map = {
        pikepdf.Name("/H1"): 1,
        pikepdf.Name("/H2"): 2,
        pikepdf.Name("/H3"): 3,
        pikepdf.Name("/H4"): 4,
        pikepdf.Name("/H5"): 5,
        pikepdf.Name("/H6"): 6,

    }

    def recurse_k_nodes(node):

        if isinstance(node, Dictionary):
            if "/K" in node.keys():
                recurse_k_nodes(node.get('/K'))
                if "/S" in node.keys():
                    if node.get("/S") in headings_map.keys():
                        headings.append(headings_map[node.get("/S")])


        if isinstance(node, Array):
            for each in node:
                if isinstance(each, Dictionary):
                    if "/K" in each.keys():
                        recurse_k_nodes(each.get("/K"))
                    if "/S" in each.keys():
                        if each.get("/S") in headings_map.keys():

                            headings.append(headings_map[each.get("/S")])

                if isinstance(each, Array):
                    recurse_k_nodes(each)

    recurse_k_nodes(root)

    # Matterhorn 14-001, 14-002, 14-003
    print("Headings Map", headings)
    if len(headings) == 0:
        return False

    if len(list(filter(lambda n: n == 1, headings))) > 1:  # greater than 1 H1 heading
        return False

    if len(headings) > 0:
        if headings[0] != 1:
            return False

    for i, h in enumerate(headings):
        if i + 1 == len(headings):
            break
        if (headings[i + 1] - h) > 1:
            return False

    return True



def check_metadata(document):

    # approved pdf accessibility tools get an auto pass if they created the pdf
    approved_pdf_exporters = [
        "Equidox 7",
    ]

    meta = {
        "title": False,
        "language": False,
        "approved_pdf_exporter": False
    }

    metadata = document.open_metadata()
    print(metadata)
    if isinstance(document.Root.get("/Lang"), Object):
        meta["language"] = True
    if metadata.get("dc:title"):
        meta["title"] = True

    producer = metadata.get("pdf:Producer")
    print(producer)
    if producer in approved_pdf_exporters:
        meta["approved_pdf_exporter"] = True

    return meta

def get_doc_data(document):

    doc_data = {
        "pages":len(document.pages)
    }
    return doc_data


def check_for_forms(document):


    for page in document.pages:

        # Attempt to access annotations for the current page
        if '/Annots' in page:
            annots = page['/Annots']

            for annot in annots:
                # Check if the annotation has the /FT key, indicating it's a form field
                if '/FT' in annot:
                    return True  # A form field was found

    # If we reach this point, no form fields were found
    return False


def check_bookmarks(document):
    if check_if_tagged(document):
        outlines = document.Root.get("/Outlines")
        # print(repr(outlines))
        if outlines:
            if outlines.get("/Count"):
                if outlines.get("/Count") > 0:
                    return True
                else:
                    return False
            else:
                if outlines.get("/First"):
                    return True
                else:
                    return False
        else:
            return False
    else:
        return False


def pdf_check(location):

    try:
        Pikepdf = Pdf.open(location, allow_overwriting_input=True)
        tagged = check_if_tagged(Pikepdf)
        # get file hash
        with open(location, 'rb') as afile:
            buf = afile.read()
            hasher = hashlib.sha256()
            hasher.update(buf)
            file_hash = hasher.hexdigest()

        if tagged:
            alt_tag_count = check_for_alt_tags(Pikepdf)
        else:
            alt_tag_count = []
        pdf_text_type = pdf_status(location)

        obj = {

            "tagged": bool(tagged),
            "has_form": check_for_forms(Pikepdf),
            # "alt_tag_count": alt_tag_count,
            "pdf_text_type": pdf_text_type,
            "metadata": check_metadata(Pikepdf),
            "doc_data": get_doc_data(Pikepdf),
            "file_hash": file_hash,

            # "headings_pass": verify_headings(Pikepdf),
            # "has_bookmarks": check_bookmarks(Pikepdf)

        }
    except PdfError as e:
        print("PDF READ ERROR", e)
        return None

    try:
        # Pikepdf.save()
        Pikepdf.close()
        return obj
    except PdfError as e:
        print("PDF WRITE ERROR", e)
        return None



