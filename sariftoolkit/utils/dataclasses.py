import logging


def _dataclass_from_dict(klass, dikt):
    try:
        fieldtypes = klass.__annotations__
        data = {}
        for f in dikt:
            if f in fieldtypes:
                data[f] = _dataclass_from_dict(fieldtypes[f], dikt[f])
            else:
                # print(f"Ignore value: {f} ({klass})")
                holder = klass.__holders__.get(f)
                if holder:
                    data[holder] = _dataclass_from_dict(klass.__holders__[f], dikt[f])

        # return klass(**{f: _dataclass_from_dict(fieldtypes[f], dikt[f]) })
        return klass(**data)

    except KeyError as err:
        raise err

    except AttributeError as err:
        if isinstance(dikt, (str, int, float, bool)):
            return dikt
        elif isinstance(dikt, (tuple, list)):
            return [_dataclass_from_dict(klass.__args__[0], f) for f in dikt]

        logging.warning(f"DataClass loading: {klass}")
        logging.warning(f"AttributeError: {err}")
        return dikt
