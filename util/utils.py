def keys_to_lower(mydict):
    newdict = {}
    for k in mydict.keys():
        if isinstance(mydict[k], dict):
            newdict[k.lower()] = keys_to_lower(mydict[k])
        else:
            if isinstance(mydict[k], list):
                newdict[k.lower()] = [keys_to_lower(i) if isinstance(i, dict) else i for i in mydict[k]]
            else:
                newdict[k.lower()] = mydict[k]

    return newdict