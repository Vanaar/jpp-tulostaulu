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
    palot VARCHAR(10),
    luotu TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ottelunumero)
);

INSERT INTO otteludata (ottelunumero, kotijoukkue, vierasjoukkue, jakso_0_koti_juoksut, jakso_0_vieras_juoksut, jakso_1_koti_juoksut, jakso_1_vieras_juoksut, jakso_2_koti_juoksut, jakso_2_vieras_juoksut, jakso_3_koti_juoksut, jakso_3_vieras_juoksut, koti_jaksovoitot, vieras_jaksovoitot, nykyinen_lyontivuoro, nykyinen_jakso, nykyinen_vuoropari, palot)
VALUES (1, 'Vimpelin Veto', 'Joensuun Maila', 2, 1, 0, 0, 2, 3, 1, 0, 2, 1, 'Vimpelin Veto', 3, 'toinen', '0-0');

INSERT INTO otteludata (ottelunumero, kotijoukkue, vierasjoukkue, jakso_0_koti_juoksut, jakso_0_vieras_juoksut, jakso_1_koti_juoksut, jakso_1_vieras_juoksut, jakso_2_koti_juoksut, jakso_2_vieras_juoksut, jakso_3_koti_juoksut, jakso_3_vieras_juoksut, koti_jaksovoitot, vieras_jaksovoitot, nykyinen_lyontivuoro, nykyinen_jakso, nykyinen_vuoropari, palot)
VALUES (2, 'Kankaanpään Maila', 'Hyvinkään Tahko', 0, 1, 1, 2, 0, 0, 3, 1, 1, 3, 'Kankaanpään Maila', 2, 'ensimmäinen', '1-1');

INSERT INTO otteludata (ottelunumero, kotijoukkue, vierasjoukkue, jakso_0_koti_juoksut, jakso_0_vieras_juoksut, jakso_1_koti_juoksut, jakso_1_vieras_juoksut, jakso_2_koti_juoksut, jakso_2_vieras_juoksut, jakso_3_koti_juoksut, jakso_3_vieras_juoksut, koti_jaksovoitot, vieras_jaksovoitot, nykyinen_lyontivuoro, nykyinen_jakso, nykyinen_vuoropari, palot)
VALUES (3, 'Seinäjoen Maila-Jussit', 'Siilinjärven Pesis', 3, 1, 0, 2, 1, 0, 2, 3, 2, 1, 'Siilinjärven Pesis', 4, 'toinen', '2-0');

INSERT INTO otteludata (ottelunumero, kotijoukkue, vierasjoukkue, jakso_0_koti_juoksut, jakso_0_vieras_juoksut, jakso_1_koti_juoksut, jakso_1_vieras_juoksut, jakso_2_koti_juoksut, jakso_2_vieras_juoksut, jakso_3_koti_juoksut, jakso_3_vieras_juoksut, koti_jaksovoitot, vieras_jaksovoitot, nykyinen_lyontivuoro, nykyinen_jakso, nykyinen_vuoropari, palot)
VALUES (4, 'Jyväskylän Kiri', 'Pattijoen Urheilijat', 0, 0, 1, 2, 3, 1, 1, 0, 1, 3, 'Pattijoen Urheilijat', 3, 'ensimmäinen', '0-0');

INSERT INTO otteludata (ottelunumero, kotijoukkue, vierasjoukkue, jakso_0_koti_juoksut, jakso_0_vieras_juoksut, jakso_1_koti_juoksut, jakso_1_vieras_juoksut, jakso_2_koti_juoksut, jakso_2_vieras_juoksut, jakso_3_koti_juoksut, jakso_3_vieras_juoksut, koti_jaksovoitot, vieras_jaksovoitot, nykyinen_lyontivuoro, nykyinen_jakso, nykyinen_vuoropari, palot)
VALUES (5, 'Kempeleen Kiri', 'Rauman Lukko', 1, 0, 2, 1, 0, 3, 1, 1, 2, 3, 'Rauman Lukko', 2, 'toinen', '1-0');
