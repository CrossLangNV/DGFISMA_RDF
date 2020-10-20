import os.path
from zipfile import ZipFile

import requests


def get_eurovoc_rdf():
    """ Has 3,541,287 triplets.

    :return:
    """

    media_folder = os.path.dirname(__file__)

    filename_rdf = 'eurovoc_skos.rdf'

    filename_zip = os.path.join(media_folder, 'eurovoc_skos.zip')
    url = 'http://publications.europa.eu/resource/distribution/eurovoc/20200630-0/zip/skos_xl/eurovoc_skos.zip'

    download_if_not_exists(filename_zip, url)

    filepath_rdf = os.path.join(media_folder, filename_rdf)
    if not os.path.exists(filepath_rdf):
        download_if_not_exists(filename_zip, url)

        with ZipFile(filename_zip, 'r') as zipObj:
            zipObj.extract(filename_rdf, path=media_folder)

    return filepath_rdf


def download_file(filename, url):
    """
    Download an URL to a file
    """
    with open(filename, 'wb') as fout:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        # Write response data to file
        for block in response.iter_content(2 ** 12):
            fout.write(block)


def download_if_not_exists(filename, url):
    """
    Download a URL to a file if the file
    does not exist already.
    Returns
    -------
    True if the file was downloaded,
    False if it already existed
    """
    if not os.path.exists(filename):
        download_file(filename, url)
        return True
    return False
