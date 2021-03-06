"""
Conversions between Spotify IDs, URIs and URLs.

.. currentmodule:: tekore.convert
.. autosummary::
   :nosignatures:

   ConversionError
   IdentifierType
   check_id
   check_type
   from_uri
   from_url
   to_uri
   to_url

.. code:: python

    import tekore as tk

    # Create ULR for opening an album in the browser
    mountain = '3RBULTZJ97bvVzZLpxcB0j'
    m_url = tk.to_url('album', mountain)

    # Parse input
    type_, id_ = tk.from_url(m_url)
    print(f'Got type `{type_}` with ID `{id_}`')
"""

import re

from typing import Union
from tekore.serialise import SerialisableEnum


class ConversionError(Exception):
    pass


class IdentifierType(SerialisableEnum):
    """
    Valid types of Spotify IDs.
    """
    artist = 'artist'
    album = 'album'
    episode = 'episode'
    playlist = 'playlist'
    show = 'show'
    track = 'track'


def check_type(type_: Union[str, IdentifierType]):
    """
    Validate type of an ID and raise if invalid.
    """
    if str(type_) not in IdentifierType.__members__:
        raise ConversionError(f'Invalid type "{type_}"!')


# Match beginning, all base62 characters and end of string
all_base62 = re.compile('^[0-9a-zA-Z]*$')


def check_id(id_: str):
    """
    Validate resource ID and raise if invalid.
    """
    if id_ == '' or all_base62.search(id_) is None:
        raise ConversionError(f'Invalid id: "{id_}"!')


def to_uri(type_: Union[str, IdentifierType], id_: str) -> str:
    """
    Convert an ID to an URI of the appropriate type.

    Parameters
    ----------
    type_
        valid :class:`IdentifierType`
    id_
        resource identifier

    Returns
    -------
    str
        converted URI
    """
    check_type(type_)
    check_id(id_)
    return f'spotify:{type_}:{id_}'


def to_url(type_: Union[str, IdentifierType], id_: str) -> str:
    """
    Convert an ID to an URL of the appropriate type.

    Parameters
    ----------
    type_
        valid :class:`IdentifierType`
    id_
        resource identifier

    Returns
    -------
    str
        converted URL
    """
    check_type(type_)
    check_id(id_)
    return f'https://open.spotify.com/{type_}/{id_}'


def from_uri(uri: str) -> tuple:
    """
    Parse type and ID from an URI.

    Parameters
    ----------
    uri
        URI to parse

    Returns
    -------
    tuple
        (type, ID) parsed from the URI
    """
    spotify, type_, id_ = uri.split(':')

    if spotify != 'spotify':
        raise ConversionError(f'Invalid URI prefix "{spotify}"!')
    check_type(type_)
    check_id(id_)

    return type_, id_


_url_prefixes = (
    'open.spotify.com',
    'http://open.spotify.com',
    'https://open.spotify.com'
)


def from_url(url: str) -> tuple:
    """
    Parse type and ID from an URL.

    Parameters
    ----------
    url
        URL to parse

    Returns
    -------
    tuple
        (type, ID) parsed from the URL
    """
    *prefixes, type_, id_ = url.split('/')
    prefix = '/'.join(prefixes)

    if prefix not in _url_prefixes:
        raise ConversionError(f'Invalid URL prefix "{prefix}"!')
    check_type(type_)
    check_id(id_)

    return type_, id_
