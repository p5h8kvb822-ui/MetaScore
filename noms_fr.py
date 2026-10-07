"""Noms en français : pays / sélections, clubs courants et compétitions.
Les noms absents de ces listes restent tels que l'API les donne (à compléter au besoin)."""

PAYS = {
    "Albania": "Albanie", "Algeria": "Algérie", "Argentina": "Argentine", "Armenia": "Arménie",
    "Australia": "Australie", "Austria": "Autriche", "Azerbaijan": "Azerbaïdjan", "Belarus": "Biélorussie",
    "Belgium": "Belgique", "Bolivia": "Bolivie", "Bosnia and Herzegovina": "Bosnie-Herzégovine",
    "Bosnia-and-Herzegovina": "Bosnie-Herzégovine", "Brazil": "Brésil", "Bulgaria": "Bulgarie",
    "Cameroon": "Cameroun", "Cape Verde": "Cap-Vert", "Chile": "Chili", "China": "Chine", "Colombia": "Colombie",
    "Costa Rica": "Costa Rica", "Croatia": "Croatie", "Cyprus": "Chypre", "Czech Republic": "Tchéquie",
    "Czech-Republic": "Tchéquie", "Czechia": "Tchéquie", "Denmark": "Danemark", "DR Congo": "RD Congo",
    "Congo DR": "RD Congo", "Ecuador": "Équateur", "Egypt": "Égypte", "England": "Angleterre",
    "Estonia": "Estonie", "Finland": "Finlande", "Georgia": "Géorgie", "Germany": "Allemagne", "Ghana": "Ghana",
    "Greece": "Grèce", "Hungary": "Hongrie", "Iceland": "Islande", "Iran": "Iran", "Iraq": "Irak",
    "Ireland": "Irlande", "Israel": "Israël", "Italy": "Italie", "Ivory Coast": "Côte d'Ivoire",
    "Ivory-Coast": "Côte d'Ivoire", "Jamaica": "Jamaïque", "Japan": "Japon", "Kazakhstan": "Kazakhstan",
    "Kosovo": "Kosovo", "Latvia": "Lettonie", "Lithuania": "Lituanie", "Luxembourg": "Luxembourg",
    "Mali": "Mali", "Malta": "Malte", "Mexico": "Mexique", "Moldova": "Moldavie", "Montenegro": "Monténégro",
    "Morocco": "Maroc", "Netherlands": "Pays-Bas", "New Zealand": "Nouvelle-Zélande", "Nigeria": "Nigeria",
    "North Macedonia": "Macédoine du Nord", "Northern Ireland": "Irlande du Nord", "Northern-Ireland": "Irlande du Nord",
    "Norway": "Norvège", "Paraguay": "Paraguay", "Peru": "Pérou", "Poland": "Pologne", "Portugal": "Portugal",
    "Qatar": "Qatar", "Romania": "Roumanie", "Russia": "Russie", "Saudi Arabia": "Arabie saoudite",
    "Saudi-Arabia": "Arabie saoudite", "Scotland": "Écosse", "Senegal": "Sénégal", "Serbia": "Serbie",
    "Slovakia": "Slovaquie", "Slovenia": "Slovénie", "South Africa": "Afrique du Sud", "South Korea": "Corée du Sud",
    "South-Korea": "Corée du Sud", "Spain": "Espagne", "Sweden": "Suède", "Switzerland": "Suisse",
    "Tunisia": "Tunisie", "Turkey": "Turquie", "Türkiye": "Turquie", "Ukraine": "Ukraine", "Uruguay": "Uruguay",
    "USA": "États-Unis", "United States": "États-Unis", "Uzbekistan": "Ouzbékistan", "Venezuela": "Venezuela",
    "Wales": "Pays de Galles",
}

CLUBS = {
    "Paris Saint Germain": "Paris SG", "Paris Saint-Germain": "Paris SG", "Paris Saint Germain FC": "Paris SG",
    "Olympique Lyonnais": "Lyon", "Olympique De Marseille": "Marseille", "Olympique Marseille": "Marseille",
    "AS Monaco": "Monaco", "Stade Rennais": "Rennes", "Saint Etienne": "Saint-Étienne", "St Etienne": "Saint-Étienne",
    "Stade Brestois 29": "Brest", "RC Strasbourg": "Strasbourg", "Racing Club De Lens": "Lens",
    "Bayern Munich": "Bayern Munich", "Borussia Dortmund": "Dortmund", "Bayer Leverkusen": "Leverkusen",
    "RB Leipzig": "Leipzig", "Eintracht Frankfurt": "Francfort", "FC Koln": "Cologne", "1. FC Köln": "Cologne",
    "Borussia Monchengladbach": "Mönchengladbach", "Borussia Mönchengladbach": "Mönchengladbach",
    "VfB Stuttgart": "Stuttgart", "VfL Wolfsburg": "Wolfsburg", "Werder Bremen": "Brême", "SC Freiburg": "Fribourg",
    "Inter": "Inter Milan", "AC Milan": "Milan AC", "AS Roma": "Rome", "Roma": "Rome", "Napoli": "Naples",
    "Lazio": "Lazio Rome", "Genoa": "Gênes", "Sevilla": "Séville", "Atletico Madrid": "Atlético Madrid",
    "Athletic Club": "Athletic Bilbao", "Real Betis": "Betis Séville", "Valencia": "Valence",
    "Sporting CP": "Sporting", "FC Porto": "Porto", "SL Benfica": "Benfica", "PSV Eindhoven": "PSV",
    "Club Brugge KV": "FC Bruges", "Club Brugge": "FC Bruges", "Red Bull Salzburg": "Salzbourg",
    "FC Basel": "Bâle", "Basel": "Bâle", "FC Copenhagen": "Copenhague", "Copenhagen": "Copenhague",
    "Shakhtar Donetsk": "Chakhtar Donetsk", "Dynamo Kyiv": "Dynamo Kiev", "Red Star Belgrade": "Étoile Rouge de Belgrade",
    "Slavia Praha": "Slavia Prague", "Sparta Praha": "Sparta Prague", "Legia Warszawa": "Legia Varsovie",
    "Olympiakos Piraeus": "Olympiakos", "Fenerbahce": "Fenerbahçe", "Bodo/Glimt": "Bodø/Glimt",
    "Manchester United": "Manchester United", "Manchester City": "Manchester City", "Newcastle": "Newcastle",
    "Wolves": "Wolverhampton", "Nottingham Forest": "Nottingham Forest",
}

COMPETITIONS = {
    "UEFA Champions League": "Ligue des champions", "UEFA Europa League": "Ligue Europa",
    "UEFA Europa Conference League": "Ligue Conférence", "UEFA Conference League": "Ligue Conférence",
    "UEFA Nations League": "Ligue des nations", "Friendlies": "Matchs amicaux", "Friendlies Clubs": "Matchs amicaux de clubs",
    "World Cup": "Coupe du monde", "Euro Championship": "Championnat d'Europe",
    "World Cup - Qualification Europe": "Éliminatoires Coupe du monde (Europe)",
    "Euro Championship - Qualification": "Éliminatoires Euro", "FA Cup": "FA Cup", "Coupe de France": "Coupe de France",
    "Copa del Rey": "Coupe du Roi", "DFB Pokal": "Coupe d'Allemagne", "Coppa Italia": "Coupe d'Italie",
}


def _lookup(table, name):
    if not name:
        return name
    if name in table:
        return table[name]
    low = {k.lower(): v for k, v in table.items()}
    return low.get(name.lower(), name)


def fr_pays(name):
    return _lookup(PAYS, name)


def fr_team(name):
    """Sélections nationales -> pays en français ; clubs courants -> nom français ; sinon inchangé."""
    out = _lookup(PAYS, name)
    return out if out != name else _lookup(CLUBS, name)


def fr_comp(name):
    return _lookup(COMPETITIONS, name)
