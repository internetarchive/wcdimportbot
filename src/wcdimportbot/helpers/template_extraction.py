import logging
import re
from collections import OrderedDict
from typing import List
from typing import OrderedDict as OrderedDictType
from typing import Tuple

import mwparserfromhell  # type: ignore

# This code has been snipped from pywikibot 7.2.0 textlib.py to avoid forking the whole thing
import config

ETPType = List[Tuple[str, OrderedDictType[str, str]]]

logging.basicConfig(level=config.loglevel)
logger = logging.getLogger(__name__)


def remove_comments(text: str):
    """Remove html comments <!-- -->
    Copyright Dennis Priskorn"""
    # This regex tries to match text on both sides of
    # the comment and join them or in the case no comment is found
    # just return the whole thing.
    regex = re.compile(r"(.*)<!--.*-->(.*)|(.*)")
    matches = re.findall(pattern=regex, string=text)
    if matches:
        # print(match.groups())
        string = ""
        for match in matches:
            # print(match)
            if match:
                for part in match:
                    string += str(part)
        return string.strip()
    else:
        return text


def extract_templates_and_params(text: str, strip: bool = False) -> ETPType:
    """Return a list of templates found in text.

    Return value is a list of tuples. There is one tuple for each use of a
    template in the page, with the template title as the first entry and a
    dict of parameters as the second entry. Parameters are indexed by
    strings; as in MediaWiki, an unnamed parameter is given a parameter name
    with an integer value corresponding to its position among the unnamed
    parameters, and if this results multiple parameters with the same name
    only the last value provided will be returned.

    This uses the package :py:obj:`mwparserfromhell` or
    :py:obj:`wikitextparser` as MediaWiki markup parser. It is mandatory
    that one of them is installed.

    There are minor differences between the two implementations.

    The parser packages preserves whitespace in parameter names and
    values.

    If there are multiple numbered parameters in the wikitext for the
    same position, MediaWiki will only use the last parameter value.
    e.g. `{{a| foo | 2 <!-- --> = bar | baz }}` is `{{a|1=foo|2=baz}}`
    To replicate that behaviour, enable both `remove_disabled_parts`
    and `strip` parameters.

    :param text: The wikitext from which templates are extracted
    :param strip: If enabled, strip arguments and values of templates.
    :return: list of template name and params

    .. versionchanged:: 6.1
       *wikitextparser* package is supported; either *wikitextparser* or
       *mwparserfromhell* is strictly recommended.
    """

    def explicit(param):
        try:
            attr = param.showkey
        except AttributeError:
            attr = not param.positional
        return attr

    # This has been disabled by Dennis Priskorn
    # because it is not KISS and it relies on half of
    # pywikibot and we probably don't need it because
    # references are probably never inside disabled parts like "nowiki".
    # if remove_disabled_parts:
    #     text = removeDisabledParts(text)

    result = []
    parsed = mwparserfromhell.parse(text)

    templates = parsed.ifilter_templates(
        matches=lambda x: not x.name.lstrip().startswith("#"), recursive=True
    )
    arguments = "params"

    for template in templates:
        params = OrderedDict()
        for param in getattr(template, arguments):
            value = str(param.value)  # mwpfh needs upcast to str
            if strip:
                key = param.name.strip()
                if explicit(param):
                    value = param.value.strip()
                else:
                    value = str(param.value)
            else:
                key = str(param.name)
            # Remove comments
            # logger.debug(f"value before: {value}")
            value = remove_comments(value)
            # logger.debug(f"value after: {value}")
            params[key] = value

        result.append((template.name.strip(), params))
    return result
