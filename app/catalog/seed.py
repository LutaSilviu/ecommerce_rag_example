"""Stable Romanian demo catalog used to populate the persistent catalog tables.

Product and category UUIDs are intentionally stable: browser carts and historical
order snapshots may retain product IDs between application restarts.
"""

from types import MappingProxyType
from typing import Mapping
from uuid import UUID

from app.catalog.taxonomy import CATEGORIES
from app.domain.models import Category, Product


def _uuid(kind: str, number: int) -> UUID:
    prefix = "a1" if kind == "category" else "b2"
    return UUID(f"{prefix}000000-0000-4000-8000-{number:012d}")


def _product_uuid(number: int) -> UUID:
    """Keep legacy product IDs 1–12 and reserve a separate stable range for additions."""
    if number <= 12:
        return _uuid("product", number)
    return UUID(f"b3000000-0000-4000-8000-{number - 12:012d}")


CATEGORY_IDS: Mapping[str, UUID] = MappingProxyType(
    {definition.slug: _uuid("category", index) for index, definition in enumerate(CATEGORIES, 1)}
)

CATEGORY_SEEDS: tuple[Category, ...] = tuple(
    Category(
        id=CATEGORY_IDS[definition.slug],
        slug=definition.slug,
        name=definition.name_ro,
        description=definition.description_ro,
        sort_order=definition.sort_order,
        is_active=True,
    )
    for definition in CATEGORIES
)


def _photo(photo_id: str) -> str:
    return f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w=900&q=80"


# sku, category, slug, name, description, price in bani, image, stock
_ROWS = (
    ('ELE', 'electronics', 'casti-audio-urban', 'Căști wireless Urban', 'Căști Bluetooth confortabile, cu autonomie de până la 30 de ore și microfon pentru apeluri clare.', 24990, 'photo-1505740420928-5e560c06d30e', 18),
    ('ELE', 'electronics', 'boxa-portabila-mini', 'Boxă portabilă Mini', 'Boxă compactă pentru acasă sau călătorii, cu conexiune Bluetooth și baterie reîncărcabilă.', 17990, 'photo-1608043152269-423dbba4e7e1', 11),
    ('ELE', 'electronics', 'incarcator-usb-c-65w', 'Încărcător USB-C 65 W', 'Încărcător compact cu port USB-C, potrivit pentru telefoane, tablete și laptopuri compatibile.', 12990, 'photo-1583863788434-e58a36330cf0', 24),
    ('HOM', 'home', 'lampa-de-birou-led', 'Lampă de birou LED', 'Lampă cu braț reglabil și lumină caldă, ideală pentru colțul de lucru sau noptieră.', 15990, 'photo-1507473885765-e6ed057f782c', 9),
    ('HOM', 'home', 'cana-ceramica-sand', 'Cană ceramică Sand', 'Cană din ceramică cu finisaj mat și formă simplă, pentru cafeaua sau ceaiul de zi cu zi.', 4990, 'photo-1514228742587-6b1558fcca3d', 32),
    ('HOM', 'home', 'organizator-birou-lemn', 'Organizator de birou din lemn', 'Suport cu compartimente pentru pixuri, notițe și accesorii mici, realizat din lemn natur.', 8990, 'photo-1494438639946-1ebd1d20bf85', 12),
    ('FAS', 'fashion', 'tricou-bumbac-essential', 'Tricou Essential din bumbac', 'Tricou cu croială lejeră, din bumbac moale, ușor de purtat în ținute casual.', 7990, 'photo-1521572163474-6864f9cf17ab', 27),
    ('FAS', 'fashion', 'rucsac-city-compact', 'Rucsac City Compact', 'Rucsac urban ușor, cu buzunar interior pentru laptop și compartiment frontal cu fermoar.', 18990, 'photo-1553062407-98eeb64c6a62', 7),
    ('FAS', 'fashion', 'geanta-crossbody-amelie', 'Geantă crossbody Amélie', 'Geantă compactă cu curea reglabilă și închidere cu fermoar, potrivită pentru ieșirile zilnice.', 13990, 'photo-1548036328-c9fa89d128fa', 5),
    ('CAR', 'personal-care', 'crema-hidratanta-zilnica', 'Cremă hidratantă pentru față', 'Cremă cu textură ușoară pentru rutina zilnică, potrivită pentru hidratarea tenului normal.', 6990, 'photo-1608248543803-ba4f8c70ae0b', 16),
    ('CAR', 'personal-care', 'gel-de-dus-citrice', 'Gel de duș cu note citrice', 'Gel de duș cu parfum proaspăt de citrice și formulă delicată pentru folosirea de zi cu zi.', 2990, 'photo-1608571423902-eed4a5ad8108', 21),
    ('CAR', 'personal-care', 'set-ingrijire-mainilor', 'Set pentru îngrijirea mâinilor', 'Set cadou cu cremă de mâini și săpun lichid, cu parfum discret și ambalaj simplu.', 5490, 'photo-1556229010-6c3f2c9ca5f8', 10),
    ('ELE', 'electronics', 'mouse-wireless-silent', 'Mouse wireless Silent', 'Mouse optic fără fir, cu clicuri silențioase, receptor USB și formă comodă pentru lucrul de zi cu zi.', 8990, 'photo-1527864550417-7fd91fc51a46', 20),
    ('ELE', 'electronics', 'tastatura-compacta', 'Tastatură compactă', 'Tastatură cu conectare USB și format compact, utilă pentru birouri unde spațiul contează.', 13990, 'photo-1587829741301-dc798b83add3', 14),
    ('ELE', 'electronics', 'suport-laptop-aluminiu', 'Suport laptop din aluminiu', 'Suport stabil cu înălțime reglabilă, pentru o poziție de lucru mai comodă acasă sau la birou.', 11990, 'photo-1527864550417-7fd91fc51a46', 8),
    ('HOM', 'home', 'patura-moale-nordic', 'Pătură moale Nordic', 'Pătură ușoară și plăcută la atingere, potrivită pentru serile răcoroase și un plus de culoare în living.', 12990, 'photo-1600210492486-724fe5c67fb0', 13),
    ('HOM', 'home', 'vaza-ceramica-arc', 'Vază ceramică Arc', 'Vază decorativă cu profil simplu, potrivită pentru flori proaspete sau ca accent pe raft.', 7990, 'photo-1578500494198-246f612d3b3d', 6),
    ('HOM', 'home', 'perna-decorativa-linen', 'Pernă decorativă Linen', 'Pernă cu husă texturată și aspect natural, ușor de integrat pe canapea sau pe pat.', 6990, 'photo-1584100936595-c0654b55a2e2', 15),
    ('FAS', 'fashion', 'hanorac-cotton-weekend', 'Hanorac Cotton Weekend', 'Hanorac confortabil din bumbac, cu glugă și buzunar frontal, pentru ținute relaxate.', 16990, 'photo-1556821840-3a63f4a1f2c1', 10),
    ('FAS', 'fashion', 'sapca-basic', 'Șapcă Basic', 'Șapcă reglabilă cu cozoroc curbat, accesoriu practic pentru plimbări și zile însorite.', 5990, 'photo-1588850561407-ed78c282e89b', 19),
    ('FAS', 'fashion', 'portofel-slim', 'Portofel Slim', 'Portofel subțire cu compartimente pentru carduri și bancnote, ușor de purtat în buzunar.', 8990, 'photo-1627123424574-724758594e93', 8),
    ('CAR', 'personal-care', 'sampon-usoara-hidratare', 'Șampon Hidratare Ușoară', 'Șampon pentru utilizare frecventă, cu parfum proaspăt și recipient practic de 300 ml.', 4490, 'photo-1608248543803-ba4f8c70ae0b', 17),
    ('CAR', 'personal-care', 'balsam-buze-cirese', 'Balsam de buze cu cireșe', 'Balsam compact pentru buze, cu aromă discretă de cireșe și aplicare ușoară oriunde te afli.', 1990, 'photo-1608248543803-ba4f8c70ae0b', 25),
    ('CAR', 'personal-care', 'perie-par-lemn', 'Perie de păr din lemn', 'Perie cu mâner din lemn și peri flexibili, concepută pentru descurcarea delicată a părului.', 7990, 'photo-1522337360788-8b13dee7a37e', 7),
    ('SPT', 'sports', 'saltea-fitness-fold', 'Saltea fitness Fold', 'Saltea pliabilă cu suprafață aderentă, ușor de strâns după exerciții și potrivită pentru acasă.', 11990, 'photo-1518611012118-696072aa579a', 14),
    ('SPT', 'sports', 'bidon-termo-750', 'Bidon termoizolant 750 ml', 'Bidon reutilizabil cu perete termoizolant și capac etanș, util la antrenament sau în drum.', 8990, 'photo-1602143407151-7111542de6e8', 18),
    ('SPT', 'sports', 'benzi-elastice-set', 'Set benzi elastice fitness', 'Trei benzi cu niveluri diferite de rezistență pentru exerciții de mobilitate și antrenament.', 6990, 'photo-1599058917212-d750089bc07a', 22),
    ('SPT', 'sports', 'minge-fotbal-training', 'Minge de fotbal Training', 'Minge rezistentă pentru antrenamente recreative în parc sau pe terenul de sport.', 9990, 'photo-1614632537423-1e6c2e7e0b34', 0),
    ('TOY', 'toys', 'set-constructie-color', 'Set de construcție Color', 'Piese colorate pentru construcții libere și jocuri creative, într-o cutie ușor de depozitat.', 12990, 'photo-1587654780291-39c9404d746b', 12),
    ('TOY', 'toys', 'puzzle-peisaj-500', 'Puzzle Peisaj, 500 piese', 'Puzzle ilustrat cu 500 de piese, potrivit pentru o activitate liniștită în familie.', 5990, 'photo-1606503153255-59d8b8b82179', 9),
    ('TOY', 'toys', 'joc-memorie-familie', 'Joc de memorie pentru familie', 'Joc compact cu cartonașe ilustrate, simplu de învățat și potrivit pentru mai multe vârste.', 4490, 'photo-1610890716171-6b1bb98ffd09', 16),
    ('TOY', 'toys', 'masinuta-lemn', 'Mașinuță din lemn', 'Jucărie din lemn cu roți mobile și margini rotunjite, potrivită pentru joaca de zi cu zi.', 3990, 'photo-1594787318286-3d835c1d207f', 11),
    ('BOK', 'books', 'agenda-saptamanala', 'Agendă săptămânală', 'Agendă nedatată cu pagini pentru planuri, liste și notițe, în format ușor de luat în geantă.', 4990, 'photo-1531346878377-a5be20888e57', 20),
    ('BOK', 'books', 'caiet-notite-a5', 'Caiet de notițe A5', 'Caiet cu copertă rigidă și pagini liniate, pentru idei, întâlniri sau notițe de curs.', 2990, 'photo-1531346878377-a5be20888e57', 30),
    ('BOK', 'books', 'set-markere-pastel', 'Set markere pastel', 'Set cu șase markere în culori pastel, potrivite pentru evidențieri, schițe și bullet journal.', 3990, 'photo-1455390582262-044cdead277a', 13),
    ('BOK', 'books', 'semn-de-carte-metal', 'Semn de carte metalic', 'Semn de carte subțire, cu finisaj metalic, pentru a regăsi rapid pagina la care ai rămas.', 2490, 'photo-1519682337058-a94d519337bc', 0),
    ('KIT', 'kitchen', 'set-linguri-masurare', 'Set linguri de măsurare', 'Set compact de linguri gradate pentru dozarea ingredientelor în rețete și băuturi.', 3490, 'photo-1556911220-e15b29be8c8f', 17),
    ('KIT', 'kitchen', 'tocator-bambus', 'Tocător din bambus', 'Tocător practic din bambus, cu suprafață generoasă pentru pregătirea legumelor și a fructelor.', 7990, 'photo-1556911220-e15b29be8c8f', 8),
    ('KIT', 'kitchen', 'recipient-sticla', 'Recipient din sticlă cu capac', 'Recipient reutilizabil pentru păstrarea ingredientelor uscate, cu capac și corp transparent.', 5990, 'photo-1602143407151-7111542de6e8', 14),
    ('KIT', 'kitchen', 'spatula-silicon', 'Spatulă din silicon', 'Spatulă flexibilă cu mâner comod, potrivită pentru amestecare și pentru vase cu suprafață antiaderentă.', 2490, 'photo-1556911220-e15b29be8c8f', 23),
    ('ELE', 'electronics', 'smartphone-echo-8gb', 'Smartphone Echo 8 GB', 'Telefon smartphone demo cu 8 GB RAM, ecran de 6.5 inch, stocare de 128 GB si baterie pentru utilizare zilnica.', 89990, 'photo-1511707171634-5f897ff02aa9', 6),
)

PRODUCT_SLUGS: Mapping[UUID, str] = MappingProxyType(
    {_product_uuid(index): row[2] for index, row in enumerate(_ROWS, 1)}
)

PRODUCT_SEEDS: tuple[Product, ...] = tuple(
    Product(
        id=_product_uuid(index),
        sku=f"NM-{row[0]}-{sum(1 for prior in _ROWS[:index] if prior[1] == row[1]):03d}",
        category_id=CATEGORY_IDS[row[1]],
        name=row[3],
        description=row[4],
        price_bani=row[5],
        image_url=_photo(row[6]),
        stock_quantity=row[7],
        is_active=True,
    )
    for index, row in enumerate(_ROWS, 1)
)
