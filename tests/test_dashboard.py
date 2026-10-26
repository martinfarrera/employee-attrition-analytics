"""Check the offline demo against its checked-in aggregate sources."""
import csv
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "reports/dashboard/index.html"


def page():
    return ET.fromstring(PAGE.read_text())


def test_visible_numbers_match_aggregate_tables():
    document = page()
    with (ROOT / "reports/data/overview.csv").open() as source:
        overview = next(csv.DictReader(source))
    assert document.find(".//*[@id='total']").text == f"{int(overview['rows']):,}"
    assert document.find(".//*[@id='rate']").text == overview['attrition_percent'] + "%"
    with (ROOT / "reports/data/attrition-counts.csv").open() as source:
        expected = [[row['attrition'], f"{int(row['count']):,}", row['percent'] + "%"]
                    for row in csv.DictReader(source)]
    actual = [[cell.text for cell in row] for row in document.findall('.//tbody/tr')]
    assert actual == expected


def test_offline_resources_and_accessible_structure():
    document = page()
    assert document.attrib['lang'] == 'en'
    assert document.find('.//title').text
    assert document.find('.//meta[@name="viewport"]') is not None
    assert document.find('.//h1').text == 'Employee attrition overview'
    assert document.find('.//table/caption').text
    assert all(cell.attrib.get('scope') == 'col' for cell in document.findall('.//thead/tr/th'))
    assert document.find('.//script') is None
    assert document.find('.//link') is None
    for element in document.iter():
        assert not any(key.startswith('on') for key in element.attrib)
        if 'src' in element.attrib:
            assert element.tag == 'img'
            assert element.attrib['src'] == '../figures/attrition.svg'
            assert element.attrib.get('alt')
            assert (PAGE.parent / element.attrib['src']).is_file()
    css = document.find('.//style').text.lower()
    assert 'url(' not in css and '@import' not in css


def test_evidence_links_attribution_and_limits():
    document = page()
    links = {element.attrib['href'] for element in document.findall('.//a')}
    for relative in ('../data/overview.csv', '../data/attrition-counts.csv', '../attrition-eda.md'):
        assert relative in links
        assert (PAGE.parent / relative).is_file()
    text = ' '.join(document.itertext())
    for phrase in ('fictional', 'not causal', 'individual employment decisions',
                   'not an annual attrition rate', 'ODbL', 'DbCL', 'IBM HR Analytics'):
        assert phrase in text
    assert 'https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset' in links
    assert 'https://opendatacommons.org/licenses/odbl/1-0/' in links
    assert 'https://opendatacommons.org/licenses/dbcl/1-0/' in links
