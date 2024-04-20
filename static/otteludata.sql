-- Luodaan otteludata-taulu
DROP TABLE otteludata;

CREATE TABLE otteludata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ottelunumero INT,
    kotijoukkue VARCHAR(255),
    vierasjoukkue VARCHAR(255),
    jakso_0_koti_juoksut INT,
    jakso_0_vieras_juoksut INT,
    jakso_1_koti_juoksut INT,
    jakso_1_vieras_juoksut INT,
    jakso_2_koti_juoksut INT,
    jakso_2_vieras_juoksut INT,
    jakso_3_koti_juoksut INT,
    jakso_3_vieras_juoksut INT,
    koti_jaksovoitot INT,
    vieras_jaksovoitot INT,
    nykyinen_lyontivuoro VARCHAR(50),
    nykyinen_jakso INT,
    nykyinen_vuoropari VARCHAR(50),
    vuoropari_nro INT,
    vuoropari_txt VARCHAR(20),
    palot VARCHAR(20),
    luotu TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ottelunumero)
);

INSERT INTO otteludata (ottelunumero, kotijoukkue, vierasjoukkue, jakso_0_koti_juoksut, jakso_0_vieras_juoksut, jakso_1_koti_juoksut, jakso_1_vieras_juoksut, jakso_2_koti_juoksut, jakso_2_vieras_juoksut, jakso_3_koti_juoksut, jakso_3_vieras_juoksut, koti_jaksovoitot, vieras_jaksovoitot, nykyinen_lyontivuoro, nykyinen_jakso, nykyinen_vuoropari, vuoropari_nro, vuoropari_txt, palot)
VALUES (123456, 'Vimpelin Veto', 'Joensuun Maila', 2, 1, 0, 0, 2, 3, 1, 0, 2, 1, 'Vimpelin Veto', 3, 1, 1, '1. aloittava', 'XX');

INSERT INTO otteludata (ottelunumero, kotijoukkue, vierasjoukkue, jakso_0_koti_juoksut, jakso_0_vieras_juoksut, jakso_1_koti_juoksut, jakso_1_vieras_juoksut, jakso_2_koti_juoksut, jakso_2_vieras_juoksut, jakso_3_koti_juoksut, jakso_3_vieras_juoksut, koti_jaksovoitot, vieras_jaksovoitot, nykyinen_lyontivuoro, nykyinen_jakso, nykyinen_vuoropari, vuoropari_nro, vuoropari_txt, palot)
VALUES (234567, 'Siilinjärven Pesis', 'Puijon Pesis', 2, 1, 0, 0, 2, 3, 1, 0, 2, 1, 'Siilinjärven Pesis', 3, 1, 1, '1. aloittava',  'XX');