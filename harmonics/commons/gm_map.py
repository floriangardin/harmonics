from harmonics.constants import INSTRUMENTS_DICT


def get_gm_number_from_name(name: str) -> int:
    return INSTRUMENTS_DICT[name][0]
