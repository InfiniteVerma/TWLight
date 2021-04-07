from django.conf import settings
import json
import os


def check_for_target_url_duplication_and_generate_error_message(
    self, partner=False, stream=False
):
    """
    Filter for partners/streams (PROXY and BUNDLE) where the
    target_url is the same as self. On filtering, if we have
    a non-zero number of matches, we generate the appropriate
    error message to be shown to the staff.

    :param self:
    :param partner:
    :param stream:
    :return:
    """
    from TWLight.resources.models import Partner, Stream

    duplicate_target_url_partners = Partner.objects.filter(
        authorization_method__in=[Partner.PROXY, Partner.BUNDLE],
        target_url=self.target_url,
    ).values_list("company_name", flat=True)
    # Exclude self from the filtered partner list, if the operation
    # is performed on Partners.
    if partner:
        duplicate_target_url_partners = duplicate_target_url_partners.exclude(
            pk=self.pk
        )

    duplicate_target_url_streams = Stream.objects.filter(
        authorization_method__in=[Partner.PROXY, Partner.BUNDLE],
        target_url=self.target_url,
    ).values_list("name", flat=True)
    # Exclude self from the filtered stream list, if the operation
    # is performed on Streams.
    if stream:
        duplicate_target_url_streams = duplicate_target_url_streams.exclude(pk=self.pk)

    partner_duplicates_count = duplicate_target_url_partners.count()
    stream_duplicates_count = duplicate_target_url_streams.count()

    if partner_duplicates_count != 0 or stream_duplicates_count != 0:
        validation_error_msg = (
            "No two or more partners/streams can have the same target url. "
            "The following partner(s)/stream(s) have the same target url: "
        )
        validation_error_msg_partners = "None"
        validation_error_msg_streams = "None"
        if partner_duplicates_count > 1:
            validation_error_msg_partners = ", ".join(duplicate_target_url_partners)
        elif partner_duplicates_count == 1:
            validation_error_msg_partners = duplicate_target_url_partners[0]
        if stream_duplicates_count > 1:
            validation_error_msg_streams = ", ".join(duplicate_target_url_streams)
        elif stream_duplicates_count == 1:
            validation_error_msg_streams = duplicate_target_url_streams[0]

        return (
            validation_error_msg
            + " Partner(s): "
            + validation_error_msg_partners
            + ". Stream(s): "
            + validation_error_msg_streams
            + "."
        )

    return None


def get_json_schema():
    """
    JSON Schema for partner description translations
    """
    from TWLight.resources.models import Partner

    no_of_partners = Partner.objects.count()
    no_of_possible_descriptions = (
        no_of_partners * 2
    ) + 1  # The extra item is the metadata key

    JSON_SCHEMA_PARTNER_DESCRIPTION = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "maxItems": no_of_possible_descriptions,
    }

    return JSON_SCHEMA_PARTNER_DESCRIPTION


def get_partner_description(
    language_code: str, partner_short_description_key: str, partner_description_key: str
):
    """
    Function that gets a partner's short description and description in the language
    set by the user. If the descriptions don't exist in that language, the default
    will be returned (English)

    Parameters
    ----------
    language_code: str
        The language code the user has selected on TWL's settings
    partner_short_description_key: str
        The partner short description key that should be found in a json file
    partner_description_key: str
        The partner description key that should be found in a json file
    Returns
    -------
    dict
    """
    descriptions = {}
    # Getting the default file in case the description does not exist in
    # the language file
    partner_default_descriptions_dict = _read_partner_description_file("en")
    partner_descriptions_dict = _read_partner_description_file(language_code)

    descriptions["short_description"] = _get_any_description(
        partner_default_descriptions_dict,
        partner_descriptions_dict,
        partner_short_description_key,
    )

    descriptions["description"] = _get_any_description(
        partner_default_descriptions_dict,
        partner_descriptions_dict,
        partner_description_key,
    )

    return descriptions


def _read_partner_description_file(language_code: str):
    """
    Reads a partner description file and returns a dictionary, if the file exists

    ----------
    language_code: str
        The language code the user has selected in their settings

    Returns
    -------
    dict
    """
    twlight_home = settings.TWLIGHT_HOME
    filepath = "{twlight_home}/locale/{language_code}/partner_descriptions.json".format(
        twlight_home=twlight_home, language_code=language_code
    )
    if os.path.isfile(filepath):
        with open(filepath, "r") as partner_descriptions_file:
            return json.load(partner_descriptions_file)
    else:
        return {}


def _get_any_description(
    partner_default_descriptions_dict: dict,
    partner_descriptions_dict: dict,
    partner_key: str,
):
    """
    Returns either the default partner description or the partner description in the
    user's language of choice

    Parameters
    ----------
    partner_default_descriptions_dict : dict
        The default descriptions dictionary.
    partner_descriptions_dict : dict
        The descriptions dictionary with descriptions in the user's preferred language
    partner_key: str
        The description key we are looking for

    Returns
    -------
    str or None
    """
    if partner_key in partner_descriptions_dict.keys():
        return partner_descriptions_dict[partner_key]
    elif partner_key in partner_default_descriptions_dict.keys():
        return partner_default_descriptions_dict[partner_key]
    else:
        return None
