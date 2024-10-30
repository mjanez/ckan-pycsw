# inbuilt libraries
from datetime import date, datetime
import yaml
import os
import pathlib
import logging
import simplejson as json
import six

# third-party libraries
from shapely.geometry import shape
from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound

# pygeometa deps
from xml.dom import minidom
from typing import Union
import re
import pkg_resources


log_module = "[template]"
APP_DIR = os.environ["APP_DIR"]
LOG_DIR = APP_DIR + "/log"
LOGGER = logging.getLogger(__name__)
SCHEMAS_CKAN = pathlib.Path(__file__).resolve().parent.parent / 'schemas/ckan'
SCHEMAS_PYGEOMETA = pathlib.Path(__file__).resolve().parent.parent / 'schemas/pygeometa'
MAPPINGS = pathlib.Path(__file__).resolve().parent.parent / 'mappings'
VERSION = pkg_resources.require('pygeometa')[0].version
DEFAULT_LABEL_LANG = 'en'

# Custom exceptions.
class MappingValueNotFoundError(Exception):
    def __init__(self, value, codelist):
        self.value = value
        self.codelist = codelist
        super().__init__(
            f"Mapping value {self.value}  not found in {self.codelist}.yaml"
            )


def render_j2_template(mcf: dict, schema_type: str, url: str = None, template_dir: str = 'iso19139_base', mappings_folder: str = 'ckan2pycsw/mappings') -> str:
    """
    Convenience function to render Jinja2 template given
    an mcf file, string, or dict

    Attributes
    ----------
    mcf: dict. Dictionary of MCF data.
    schema_type: str. Type of schema to render, 'ckan' or 'pygeometa'.
    url: str. URL of the CKAN endpoint retrieved from envvars.
    template_dir: str. Directory of schema template.
    mappings_folder: str. Folder where the mappings are stored.

    Return
    ----------
    MCF dictionary rendered with JINJA template.
    """
    FILTERS = {
        'get_mapping_value_from_yaml_list':get_mapping_value_from_yaml_list,
        'get_mapping_values_dict_from_yaml_list':get_mapping_values_dict_from_yaml_list,
        'get_mapping_value': get_mapping_value,
        'get_raw_value_from_ckan_schema': get_raw_value_from_ckan_schema,
        'get_uri_value_from_ckan_schema': get_uri_value_from_ckan_schema,
        'get_bbox': get_bbox,
        'normalize_datetime': normalize_datetime,
        'scheming_get_json_list': scheming_get_json_list,
        'scheming_get_object_list': scheming_get_object_list,
        'scheming_clean_json_list': scheming_clean_json_list,
        'normalize_charstring': normalize_charstring,
        'get_charstring': get_charstring,
        'get_distribution_language': get_distribution_language,
        'normalize_datestring': normalize_datestring,
        'prune_distribution_formats': prune_distribution_formats,
        'prune_transfer_option': prune_transfer_option,
        'escape_json': escape_json,
        'get_languages_from_dataset': get_languages_from_dataset,
        'get_language_alternate': get_language_alternate,
        'get_localized_dataset_value': get_localized_dataset_value,
    }

    LOGGER.debug('Evaluating template directory')
    if template_dir is None:
        msg = 'template_dir or schema_local required. Used "iso19139_base" as default'
        LOGGER.warn(msg)
        raise RuntimeError(msg)


    if schema_type == 'ckan':
        LOGGER.debug(f'Setting up template environment {template_dir} of type {schema_type}')
        env = Environment(loader=FileSystemLoader(os.path.join(SCHEMAS_CKAN, template_dir)), autoescape=True)

        if template_dir != "iso19139_base":
            LOGGER.debug(f'Adding CKAN Schema mapping:{template_dir}')
            ckan_schema_path = get_mapping_value(value=template_dir, codelist="ckan-pycsw_assigments",mappings_folder=mappings_folder)
            schema_file = MAPPINGS / f"{ckan_schema_path}" / "ckan_schema.yaml"
            with open(schema_file, "r", encoding='utf-8') as f:
                ckan_schema = yaml.safe_load(f)
            env.globals.update(ckan_schema=ckan_schema)

        LOGGER.debug('Adding template filters')
        env.filters.update(FILTERS)

        LOGGER.debug('Adding globals')
        env.globals.update(url=url)
        env.globals.update(mappings_folder=mappings_folder)
        env.globals.update(zip=zip)
        env.globals.update(default_label_lang=DEFAULT_LABEL_LANG)
        env.globals.update(FILTERS)

        try:
            LOGGER.debug('Loading template')
            template = env.get_template('main.j2')
        except TemplateNotFound:
            msg = 'Missing metadata template'
            LOGGER.error(msg)
            raise RuntimeError(msg)

        LOGGER.debug('Processing CKAN template to JSON')
        mcf = update_object_lists(mcf)

        try:
            # Render the template
            rendered_template = template.render(record=mcf)
            # Clean trailing commas
            cleaned_template = clean_trailing_commas(rendered_template)
            # Escape backslashes
            escaped_template = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', cleaned_template)
            # Deserialize the JSON string
            mcf_dict = json.loads(escaped_template, strict=False)
        except json.JSONDecodeError as e:
            LOGGER.error("Error deserializing the template output: %s", e)
            # Optionally: Save the problematic output for debugging
            LOGGER.error("Problematic output: %s", rendered_template)
            raise

        return mcf_dict

    if schema_type == 'pygeometa':
        LOGGER.debug(f'Setting up template environment {template_dir} of type {schema_type}')
        env = Environment(loader=FileSystemLoader(os.path.join(SCHEMAS_PYGEOMETA, template_dir)))
    
        LOGGER.debug('Adding template filters')
        env.globals.update(default_label_lang=DEFAULT_LABEL_LANG)
        env.filters['normalize_datestring'] = normalize_datestring
        env.filters['normalize_charstring'] = normalize_charstring
        env.filters['get_distribution_language'] = get_distribution_language
        env.filters['get_charstring'] = get_charstring
        env.filters['prune_distribution_formats'] = prune_distribution_formats
        env.filters['prune_transfer_option'] = prune_transfer_option
        env.filters['get_mapping_value_from_yaml_list'] = get_mapping_value_from_yaml_list
        env.globals.update(zip=zip)
        env.globals.update(mappings_folder=mappings_folder)
        env.globals.update(get_charstring=get_charstring)
        env.globals.update(normalize_datestring=normalize_datestring)
        env.globals.update(prune_distribution_formats=prune_distribution_formats)
        env.globals.update(prune_transfer_option=prune_transfer_option)
        env.globals.update(get_mapping_value_from_yaml_list=get_mapping_value_from_yaml_list)

        try:
            LOGGER.debug('Loading template')
            template = env.get_template('main.j2')
        except TemplateNotFound:
            msg = 'Missing metadata template'
            LOGGER.error(msg)
            raise RuntimeError(msg)

        LOGGER.debug('Processing Pygeometa template to XML')
        xml = template.render(record=mcf).encode('utf-8')
        #TODO: Delete Dumps to log
        #print(pretty_print(xml),  file=open(APP_DIR + '/log/demo_pygeometa.xml', 'w'))
        return pretty_print(xml, mcf['metadata']['charset'])

#--Template functions--#
def get_raw_value_from_ckan_schema(value: str, schema, field_name: str, fields_type: str = "dataset"):
    """
    Maps a source value to its corresponding raw value in a codelist based on the CKAN schema.
    
    Parameters
    ----------
    value : str. The source value that needs to be mapped to a codelist value.
    schema : dict. The CKAN schema as a dictionary.
    field_name : str. The name of the field in the CKAN schema.
    fields_type : str, optional (default="dataset"). The type of fields to consider in the CKAN schema. This can be either "dataset" or "resource".


    Return
    ----------
    The mapped value in the codelist if found, else the source value itself.
    """
    field_choices = {}
    field_type = f'{fields_type}_fields'
    field_choices = {field["field_name"]: field["choices"] for field in schema[field_type] if "field_name" in field and field.get("choices")}

    for choice in field_choices.get(field_name, []):
        if "value" in choice and choice["value"] == value:
            value = choice["value"].rsplit('/', 1)[-1]

    return value.lower()

def get_uri_value_from_ckan_schema(value: str, schema, field_name: str, fields_type: str = "dataset"):
    """
    Maps a CKAN schema field value to a codelist URI.
        
    Parameters
    ----------
    value: str. The value of the field in the CKAN schema that needs to be mapped to a URI.
    schema: dict. The CKAN schema dictionary.
    field_name: str. The name of the field in the CKAN schema that needs to be mapped to a URI.
    fields_type : str, optional (default="dataset"). Indicates whether the field is from the dataset or the resource, by default "dataset".

    Return
    ----------
    The URI corresponding to the input value in the codelist, or the original value if it is not in the codelist.
    """
    field_choices_dict = {}
    field_choices_dict = {field["field_name"]: field.get("choices", []) for field in schema.get(f"{fields_type}_fields", [])}

    choices = field_choices_dict.get(field_name, [])
    value = next((choice["value"] for choice in choices if "value" in choice and choice["value"] == value), value)

    return value

def get_mapping_value(
    value: str,
    codelist: str,
    mappings_folder: str = 'ckan2pycsw/mappings'):
    """
    Returns the mapping value in YAML for a given codelist value. 

    This function loads a YAML file from the specified mappings folder and returns the value
    for the specified codelist value. If the value is not found in the YAML file, the category itself is returned.
    
    Parameters
    ----------
    value: str. The source value that needs to be mapped to a codelist value.
    codelist : str. The name of the YAML file (without the extension) in which the codelist is defined.
    mappings_folder: str (default="ckan2pycsw/mappings"). The folder path containing the YAML files for the mappings.

    Return
    ----------
    The value of the codelist value if found in the YAML file, else the value itself.

    Raises
    ------
    MappingValueNotFoundError: ValueError. If the given value is not found in the mapping.
    """
    try:
        map_yaml = yaml.safe_load(open(os.path.join(mappings_folder, codelist + ".yaml"), encoding="utf-8"))
    except ValueError:
        raise MappingValueNotFoundError(value, codelist) from None

    return map_yaml.get(value, value)

#TODO:--Template: CKAN data--#

# Having a string, it searches a list if it exists, and returns the value

def get_mapping_value_from_yaml_list(
    value: str,
    input_field: str,
    output_field: str,
    codelist: str,
    mappings_folder: str = 'ckan2pycsw/mappings'):
    """
    Returns the mapping value in YAML for a given codelist value.

    Parameters
    ----------
    value: str. The value to map.
    input_field: str. The field name in the YAML file to search for the value.
    output_field: str. The field name in the YAML file to return as the output.
    codelist: str. The name of the codelist YAML file to use.
    mappings_folder: str. The folder where the codelist YAML files are stored. Default is 'ckan2pycsw/mappings'.
        
    Return
    ----------
    str: The mapped value found in the YAML file, or the original value if no mapping is found.
    
    Raises
    ------
    MappingValueNotFoundError: If the codelist YAML file cannot be loaded.
    """
    try:
        map_yaml = yaml.safe_load(open(os.path.join(mappings_folder, codelist + ".yaml"), encoding="utf-8"))
    except ValueError:
        raise MappingValueNotFoundError(value, codelist) from None
    
    output_value = value
    for item in map_yaml:
        if value in item[input_field]:
            if item[output_field] is not None:
                output_value = item[output_field]
            else:
                output_value = value
            break
        
    return output_value

def get_mapping_values_dict_from_yaml_list(
    value: str,
    input_field: str,
    output_field: str,
    codelist: str,
    mappings_folder: str = 'ckan2pycsw/mappings'):
    """
    Returns the mapping value in YAML for a given codelist value.

    Parameters
    ----------
    value: str. The value to map.
    input_field: str. The field name in the YAML file to search for the value.
    output_field: str. The field name in the YAML file to return as the output.
    codelist: str. The name of the codelist YAML file to use.
    mappings_folder: str. The folder where the codelist YAML files are stored. Default is 'ckan2pycsw/mappings'.
        
    Return
    ----------
    dict: The mapped value found in the YAML file, or the original value if no mapping is found.
    
    Raises
    ------
    MappingValueNotFoundError: If the codelist YAML file cannot be loaded.
    """
    try:
        map_yaml = yaml.safe_load(open(os.path.join(mappings_folder, codelist + ".yaml"), encoding="utf-8"))
    except ValueError:
        raise MappingValueNotFoundError(value, codelist) from None
    
    output_value = value
    for item in map_yaml:
        if value in item[input_field]:
            if item[output_field] is not None:
                output_value = item
            else:
                output_value = value
            break
        
    return output_value

def scheming_clean_json_list(value):
    """
    Returns the object passed serialized as a JSON list.
    :param value: The object to serialize.
    :rtype: string
    """
    try:
        if isinstance(value, str):
            value = json.loads(value, strict=False)
            out = []
            for element in value:
                # Avoid errors
                if '"' in element:
                    element=element.replace('"', '\\"')
                if 'http' in element:
                    element=element.replace(' ', '')
                out.append(element.strip())
            value = out
        else:
            value = json.loads(value, strict=False)
        return value
    
    except (TypeError, ValueError):
        return value

def scheming_get_json_list(ckan_field, data):
  """
  Accept repeating text input in the following forms and convert to a json list for storage.
  1. a list of strings, eg.
    ["Person One", "Person Two"]
  2. a single string value to allow single text fields to be
    migrated to repeating text
    "Person One"
  """
  value = data[ckan_field]
  # 1. single string to List or 2. List
  if value is not None:
    if isinstance(value, str):
        if "[" not in value:
            value = value.split(",")
        else:
            value = json.loads(value, strict=False)
    if not isinstance(value, list):
        print('expecting list of strings')

    out = []
    for element in value:
        if not element:
            continue

        if not isinstance(element, str):
            print(_('invalid type for repeating text: %r')
                                % element)
            continue
        if isinstance(element, six.binary_type):
            try:
                element = element.decode('utf-8')
                element = element.strip()
            except UnicodeDecodeError:
                print(_('invalid encoding for "%s" value')
                                    % element)
                continue

        # Avoid errors
        if '"' in element:
            element=element.replace('"', '\"')
        if 'http' in element:
            element=element.replace(' ', '')
        out.append(element)

    # Return as a JSON string list of values
    data[ckan_field] = json.dumps([v for v in out], ensure_ascii=False)

  return data[ckan_field]

def scheming_get_object_list(ckan_field, data):
    json_data = scheming_clean_json_list(data[ckan_field])
    return json_data

def process_string(s):
    if s.startswith('["') or s.endswith('"]') or s.startswith('{"') or s.endswith('"}'):
        try:
            return json.loads(s, strict=False)
        except:
            pass
    return json.dumps(s)[1:-1].replace('\\"', "'").replace('"', "'")

def update_object_lists(data):
    for key in data:
        if isinstance(data[key], str):
            data[key] = process_string(data[key])
        elif isinstance(data[key], list):
            for i in range(len(data[key])):
                if isinstance(data[key][i], str):
                    data[key][i] = process_string(data[key][i])
        elif isinstance(data[key], dict) and 'resources' in data[key]:
            for resource in data[key]['resources']:
                for k in resource:
                    if isinstance(resource[k], str):
                        resource[k] = process_string(resource[k])
    return data

def update_large_text_lists(data):
    for key in data:
        if  isinstance(data[key], str):
            if '\n' in data[key] or '\r' in data[key]:
                try:
                    data[key] = json.dumps(data[key], ensure_ascii=False)
                except:
                    pass

    return data

def scheming_valid_json_object(value):
    """Store a JSON object as a serialized JSON string
    It accepts two types of inputs:
        1. A valid serialized JSON string (it must be an object or a list)
        2. An object that can be serialized to JSON
    Returns a parsing JSON string 
    """
    if not value:
        return
    elif isinstance(value, str):
        try:
            loaded = json.loads(value, strict=False)

            return json.dumps(loaded, ensure_ascii=False)
        except (ValueError, TypeError) as e:
            pass

#--Template: manage data--#
def normalize_datetime(timestamp):
    """
    Normalize datetime to ISO 8601 format.
    
    Return
    ----------
    Parsed datetime.
    """
    if not timestamp:
        return timestamp
    parsed = datetime.fromisoformat(timestamp)
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")

def normalize_charstring(value):
        return value.replace("-", "").replace(" ", "").replace("\t", "").lower()

def get_bbox(spatial):
    """
    Get from spatial key in CKAN extras field and convert to JSON Bounding Box.

    Return
    ----------
    BBox.
    """

    return list(shape(json.loads(json.dumps(spatial))).bounds)

def get_charstring(option: Union[str, dict], language: str,
                   language_alternate: str = None) -> list:
    """
    convenience function to return unilingual or multilingual value(s)

    :param option: option value (str or dict if multilingual)
    :param language: language
    :param language_alternate: alternate language

    :returns: list of unilingual or multilingual values
    """

    if option is None:
        return [None, None]
    elif isinstance(option, str):  # unilingual
        return [option, None]
    elif isinstance(option, list):  # multilingual list
        return [option, None]
    else:  # multilingual
        return [option.get(language), option.get(language_alternate)]

def get_distribution_language(section: str) -> str:
    """
    derive language of a given distribution construct

    :param section: section name

    :returns: distribution language
    """

    try:
        return section.split('_')[1]
    except IndexError:
        return 'en'

def normalize_datestring(datestring: str, format_: str = 'default') -> str:
    """
    groks date string into ISO8601

    :param datestring: date in string representation
    :format_: datetring format ('year' or default [full])

    :returns: string of properly formatted datestring
    """

    today_and_now = datetime.utcnow()

    re1 = r'\$Date: (?P<year>\d{4})'
    re2 = r'\$Date: (?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2})'
    re3 = r'(?P<start>.*)\$Date: (?P<year>\d{4}).*\$(?P<end>.*)'

    try:
        if isinstance(datestring, date):
            if datestring.year < 1900:
                datestring2 = '{0.day:02d}.{0.month:02d}.{0.year:4d}'.format(
                    datestring)
            else:
                datestring2 = datestring.strftime('%Y-%m-%dT%H:%M:%SZ')
            if datestring2.endswith('T00:00:00Z'):
                datestring2 = datestring2.replace('T00:00:00Z', '')
            return datestring2
        elif isinstance(datestring, int) and len(str(datestring)) == 4:  # year
            return str(datestring)
        if datestring == '$date$':  # $date$ magic keyword
            return today_and_now.strftime('%Y-%m-%d')
        elif datestring == '$datetime$':  # $datetime$ magic keyword
            return today_and_now.strftime('%Y-%m-%dT%H:%M:%SZ')
        elif datestring == '$year$':  # $year$ magic keyword
            return today_and_now.strftime('%Y')
        elif '$year$' in datestring:  # $year$ magic keyword embedded
            return datestring.replace('$year$', today_and_now.strftime('%Y'))
        elif datestring.startswith('$Date'):  # svn Date keyword
            if format_ == 'year':
                mo = re.match(re1, datestring)
                return mo.group('year')
            else:  # default
                mo = re.match(re2, datestring)
                return f"{mo.group('date')}T{mo.group('time')}"
        elif '$Date' in datestring:  # svn Date keyword embedded
            if format_ == 'year':
                mo = re.match(re3, datestring)
                return f"{mo.group('start')}{mo.group('year')}{mo.group('end')}"  # noqa
    except (AttributeError, TypeError):
        raise RuntimeError(f'Invalid datestring: {datestring}')

    return datestring

def prune_distribution_formats(formats: dict) -> list:
    """
    derive a unique list of distribution formats

    :param formats: distribution formats

    :returns: unique distribution formats list
    """

    counter = 0
    formats_ = []
    unique_formats = []

    for k1, v1 in formats.items():
        row = {}
        for k2, v2 in v1.items():
            if k2.startswith('format'):
                row[k2] = v2
        formats_.append(row)

    num_elements = len(formats)

    for f in range(0, len(formats_)):
        counter += 1
        if formats_[f] not in unique_formats:
            unique_formats.append(formats_[f])
        if num_elements == counter:
            break
    return unique_formats

def prune_transfer_option(formats: dict) -> list:
    """
    derive a unique list of transfer options.
    The unique character is based on identification language

    :param formats: list of transfer options

    :returns: unique transfer options list
    """

    unique_transfer = []
    nil_reasons = ['missing',
                   'withheld',
                   'inapplicable',
                   'unknown',
                   'template']

    for k, v in formats.items():
        if language.split(";")[0] in k and language not in nil_reasons:
            unique_transfer.append(v)
        elif language in nil_reasons:
            unique_transfer.append(v)
    return unique_transfer

def pretty_print_encoding(xml: str, encoding: str = 'UTF-8') -> str:
    """
    clean up indentation and spacing

    :param xml: str of XML data

    :returns: str of pretty-printed XML data
    """

    LOGGER.debug('pretty-printing XML')
    val = minidom.parseString(xml)
    return '\n'.join([val for val in val.toprettyxml(indent=' '*2, encoding=encoding).decode(encoding).split('\n') if val.strip()])

def pretty_print(xml: str, encoding: str = 'UTF-8') -> str:
    """
    clean up indentation and spacing

    :param xml: str of XML data

    :returns: str of pretty-printed XML data
    """

    LOGGER.debug('pretty-printing XML')
    val = minidom.parseString(xml.decode(encoding))
    return '\n'.join([val for val in val.toprettyxml(indent=' '*2).split('\n') if val.strip()])  # noqa

def escape_json(value):
    """
    Escapes backslashes and other problematic characters in JSON.

    :param value: The value to escape.

    :returns: A string representing the escaped value for use in JSON.
    """
    return json.dumps(value).replace('\\', '\\\\').replace('"', '\\"')

def get_languages_from_dataset(mcf):
    # Verificar si el valor es un diccionario
    if isinstance(mcf, dict):
        # Utilizar una lista para almacenar todas las claves encontradas
        languages = []

        # Verificar si 'title_translated' existe en el diccionario
        if 'title_translated' in mcf and isinstance(mcf['title_translated'], dict):
            # Si existe, recorrer las claves de 'title_translated' y agregarlas a la lista
            for lang in mcf['title_translated'].keys():
                languages.append(lang)
        return languages
    else:
        # Si no es un diccionario, devolver una lista vacía
        return None

def get_language_alternate(default_language, languages=None):
    """
    Get the alternate language from a list of languages, excluding duplicates, and return it.
    
    :param default_language (str): The default language.
    :param languages (list): A list of language codes.

    :returns: str or None: The alternate language code, or None if no alternate language is found.
    """
    # Check if a list of languages was not provided
    if languages is None or not isinstance(languages, list):
        return None

    # Create a set to store unique languages
    unique_languages = set()

    # Initialize the alternate language as None
    language_alternate = None

    for language in languages:
        # Check if the language is unique
        if language not in unique_languages:
            unique_languages.add(language)
            # If it is different from the default language, set it as the alternate language
            if language != default_language:
                language_alternate = language

    return language_alternate

def get_localized_dataset_value(multilang_value, default_language, languages=None, only_default=False):
    """
    Extract a localized dataset value based on the provided language list.

    Args:
        multilang_value (dict or str): The dataset value, typically containing language-specific data.
        languages (list, optional): A list of language codes. If provided, the output dictionary
            will only contain keys for the specified languages.
        only_default (bool, optional): If True, return only the default language value as a string.

    Returns:
        dict or str: A dictionary with key-value pairs for the specified languages, with the default
            language as the first key, or a string if only_default is True.
    """
    if isinstance(multilang_value, str):
        return multilang_value

    # Check if the multilang_value is a dictionary
    if not isinstance(multilang_value, dict):
        return None

    # If no language list is provided, return the entire multilang_value
    if languages is None:
        return None

    # If only_default is True, return the default language value as a string
    if only_default:
        return multilang_value.get(default_language, "")

    # Create a dictionary for the output, containing only specified languages
    localized_value = {}

    # Put the default language in the output dictionary
    if default_language in multilang_value:
        localized_value[default_language] = multilang_value[default_language]

    # Iterate through the remaining languages and extract matching keys from the multilang_value
    for language in languages[1:]:
        if language in multilang_value:
            localized_value[language] = multilang_value[language]

    return localized_value

def clean_trailing_commas(json_string):
    # Removes trailing commas in objects and arrays
    json_string = re.sub(r',\s*([}\]])', r'\1', json_string)
    return json_string
