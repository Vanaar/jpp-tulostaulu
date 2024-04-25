-- Luodaan otteludata-taulu
DROP TABLE otteludata;

CREATE TABLE otteludata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ottelunumero INT,
    pesistulokset INT NOT NULL DEFAULT 0,
    kotijoukkue VARCHAR(255) NOT NULL,
    vierasjoukkue VARCHAR(255) NOT NULL,
    koti_jaksovoitot INT NULL,
    vieras_jaksovoitot INT NULL,
    jakso_1_koti_juoksut INT NOT NULL DEFAULT 0,
    jakso_1_vieras_juoksut INT NOT NULL DEFAULT 0,
    jakso_2_koti_juoksut INT NULL,
    jakso_2_vieras_juoksut INT NULL,
    jakso_3_koti_juoksut INT NULL,
    jakso_3_vieras_juoksut INT NULL,
    jakso_4_koti_juoksut INT NULL,
    jakso_4_vieras_juoksut INT NULL,
    nykyinen_lyontivuoro VARCHAR(50),
    jakso_nro INT NOT NULL DEFAULT 1,
    jakso_txt VARCHAR(20) NOT NULL DEFAULT 'J1',
    vuoropari_nro INT NOT NULL DEFAULT 1,
    vuoropari_txt VARCHAR(20) NOT NULL DEFAULT '1. aloittava',
    palot VARCHAR(20),
    otteluinfo VARCHAR(50) NULL,
    luotu TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ottelunumero)
);

INSERT INTO otteludata (ottelunumero, pesistulokset, kotijoukkue, vierasjoukkue, koti_jaksovoitot, vieras_jaksovoitot, jakso_1_koti_juoksut, jakso_1_vieras_juoksut, jakso_2_koti_juoksut, jakso_2_vieras_juoksut, jakso_3_koti_juoksut, jakso_3_vieras_juoksut, jakso_4_koti_juoksut, jakso_4_vieras_juoksut, nykyinen_lyontivuoro, jakso_nro, jakso_txt, vuoropari_nro, vuoropari_txt, palot)
VALUES (512345, 0, 'Siilinjärven Pesis', 'Puijon Pesis', 1, 2, 3, 4, 5, 6, 0, 0, 0, 0, 'Siilinjärven Pesis', 1, 'J1', 1, '1. aloittava', 'XX');

INSERT INTO otteludata (ottelunumero, pesistulokset, kotijoukkue, vierasjoukkue, koti_jaksovoitot, vieras_jaksovoitot, jakso_1_koti_juoksut, jakso_1_vieras_juoksut, nykyinen_lyontivuoro, jakso_nro, jakso_txt, vuoropari_nro, vuoropari_txt, palot)
VALUES (512346, 0, 'Vimpelin Veto', 'Sotkamon Jymy', 0, 0, 0, 0, 'Vimpelin Veto', 1, 'J1', 1, '1. aloittava', '');