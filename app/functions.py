def vuoropari_int_to_str(vuoropari_nro):
    vuoropari_dict = {
        1: "1. aloittava",
        2: "1. lopettava",
        3: "2. aloittava",
        4: "2. lopettava",
        5: "3. aloittava",
        6: "3. lopettava",
        7: "4. aloittava",
        8: "4. lopettava",
        9: "S. aloittava",
        10: "S. lopettava",
        11: "K. aloittava",
        12: "K. lopettava",
        13: "K. jatkoparit"
    }
    return vuoropari_dict.get(vuoropari_nro, "ERROR: Vuoropari")

def jakso_into_to_str(jakso_nro):
    jakso_dict = {
        1: "1. jakso",
        2: "2. jakso",
        3: "Supervuoro",
        4: "Kotiutuskisa"
    }
    return jakso_dict.get(jakso_nro, "ERROR: Jakso")

    
    