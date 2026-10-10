"""Banque de textes d'horoscope : chaque texte = phrase d'ambiance (commune) + phrase propre au signe + conseil (commun).
Les trois listes avancent à des rythmes différents : un même signe ne reçoit pas deux fois le même texte avant ~330 jours,
et deux signes n'ont jamais le même texte le même jour."""
import datetime

SIGNES = ["Bélier", "Taureau", "Gémeaux", "Cancer", "Lion", "Vierge",
          "Balance", "Scorpion", "Sagittaire", "Capricorne", "Verseau", "Poissons"]
SYMBOLES = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]

AMBIANCE = [
    "Votre curiosité est en éveil.", "Une belle énergie vous accompagne toute la journée.",
    "Le calme revient et éclaircit vos idées.", "Votre intuition est particulièrement fine aujourd'hui.",
    "Un vent de renouveau souffle sur votre quotidien.", "Vous avez le cœur léger et l'esprit vif.",
    "La confiance en vous grandit pas à pas.", "Une surprise agréable pointe le bout de son nez.",
    "Votre sens de l'écoute fait la différence.", "Les astres vous invitent à ralentir un instant.",
    "Votre charme naturel opère sans effort.", "Une page se tourne en douceur.",
    "Votre détermination impressionne votre entourage.", "L'ambiance est propice aux belles discussions.",
    "Vous retrouvez un second souffle.", "Votre créativité demande à s'exprimer.",
    "Une journée simple, mais pleine de petites victoires.", "Votre générosité ne passe pas inaperçue.",
    "Les choses se mettent en place plus vite que prévu.", "Vous êtes en phase avec vos envies profondes.",
    "Un regard neuf change votre perception d'une situation.", "L'énergie du jour vous pousse à oser.",
    "Votre patience est bientôt récompensée.", "Vous captez les bonnes ondes autour de vous.",
    "Un souvenir agréable remonte et vous réchauffe.", "Votre énergie est communicative.",
    "Le moment est venu de clarifier vos priorités.", "Vous avancez avec plus de sérénité qu'hier.",
    "Votre optimisme rassure ceux qui vous entourent.", "Une rencontre ou un message vous redonne le sourire.",
]

PAR_SIGNE = {
    "Bélier": [
        "Votre élan naturel ouvre une porte au travail.", "Un projet que vous remettiez enfin décolle.",
        "En amour, la franchise vous rapproche de l'autre.", "Votre énergie physique est au beau fixe.",
        "Un défi professionnel stimule votre ambition.", "Une initiative personnelle est bien accueillie.",
        "Côté finances, un petit gain ou une économie se profile.", "Votre leadership est remarqué par votre entourage.",
        "Un célibataire pourrait bien croiser un regard marquant.", "Une discussion directe lève un malentendu.",
        "Le sport ou le mouvement vous fait un bien fou.",
    ],
    "Taureau": [
        "Le confort et la douceur sont au programme.", "Votre persévérance porte enfin ses fruits.",
        "En amour, la tendresse prend le pas sur les mots.", "Un achat réfléchi s'avère judicieux.",
        "Votre stabilité rassure un proche en doute.", "Un bon repas ou un moment gourmand vous régénère.",
        "Côté travail, la régularité fait votre force.", "Une décision financière gagne à être prise sans hâte.",
        "Votre fidélité est appréciée à sa juste valeur.", "Un coin de nature vous apaise instantanément.",
        "Un projet à long terme avance sur de bons rails.",
    ],
    "Gémeaux": [
        "Les échanges se multiplient et nourrissent votre esprit.", "Un message attendu arrive enfin.",
        "En amour, l'humour fait mouche.", "Une idée brillante surgit au bon moment.",
        "Vos talents de communication sont très sollicités.", "Une rencontre inattendue ouvre un nouvel horizon.",
        "Côté travail, vous jonglez avec brio entre plusieurs sujets.", "Un petit voyage ou une sortie vous change les idées.",
        "Votre curiosité vous mène vers une belle découverte.", "Une conversation légère détend l'atmosphère.",
        "Un projet d'écriture ou de partage prend forme.",
    ],
    "Cancer": [
        "Votre foyer devient un véritable cocon.", "Votre sensibilité est une vraie force aujourd'hui.",
        "En amour, un geste attentionné compte plus qu'un grand discours.", "Un lien familial se renforce.",
        "Votre intuition vous guide vers le bon choix.", "Un moment de nostalgie douce vous inspire.",
        "Côté travail, votre bienveillance apaise une tension.", "Une dépense pour la maison apporte du bien-être.",
        "Un proche a besoin de votre écoute et vous l'offrez avec cœur.", "Cuisiner ou recevoir vous apporte une belle joie.",
        "Vous prenez soin de vous, et cela se voit.",
    ],
    "Lion": [
        "Vous brillez naturellement sous les projecteurs.", "Votre assurance séduit et convainc.",
        "En amour, la passion se réveille avec panache.", "Une reconnaissance professionnelle est à portée de main.",
        "Votre générosité vous attire de belles sympathies.", "Un projet créatif prend une dimension nouvelle.",
        "Côté finances, une opportunité mérite votre attention.", "Vous entraînez les autres derrière votre enthousiasme.",
        "Une invitation ou une sortie flatte votre goût du beau.", "Votre chaleur humaine réconforte un proche.",
        "Un compliment sincère vous touche plus que prévu.",
    ],
    "Vierge": [
        "Votre sens du détail fait toute la différence.", "Une organisation bien pensée vous fait gagner du temps.",
        "En amour, les petites attentions parlent d'elles-mêmes.", "Votre efficacité est saluée au travail.",
        "Un problème pratique trouve une solution élégante.", "Prendre soin de votre santé vous apporte un vrai mieux-être.",
        "Côté budget, un tri ou un bilan s'avère utile.", "Votre analyse rassure une équipe hésitante.",
        "Un rangement ou un nettoyage libère aussi votre esprit.", "Un conseil que vous donnez est précieux pour quelqu'un.",
        "Un projet précis avance grâce à votre méthode.",
    ],
    "Balance": [
        "L'harmonie revient dans vos relations.", "Votre diplomatie désamorce une situation tendue.",
        "En amour, l'équilibre se retrouve dans le dialogue.", "Une collaboration prometteuse se dessine.",
        "Votre sens esthétique vous inspire une jolie idée.", "Une décision longtemps repoussée devient évidente.",
        "Côté travail, l'esprit d'équipe porte ses fruits.", "Une sortie culturelle ou artistique vous ressource.",
        "Un geste de réconciliation est bien accueilli.", "Votre charme facilite une négociation.",
        "Une rencontre amicale apporte un souffle de légèreté.",
    ],
    "Scorpion": [
        "Votre intensité attire les confidences.", "Une vérité cachée finit par éclater au grand jour.",
        "En amour, la sincérité renforce une belle complicité.", "Votre concentration est redoutable au travail.",
        "Une transformation personnelle s'amorce doucement.", "Votre instinct vous protège d'une mauvaise surprise.",
        "Côté finances, une affaire en suspens se clarifie.", "Un secret est bien gardé et vous gagnez en confiance.",
        "Votre magnétisme ne laisse personne indifférent.", "Une page du passé se referme enfin.",
        "Une énergie profonde vous pousse à agir.",
    ],
    "Sagittaire": [
        "L'envie de voyager ou de changer d'air se fait sentir.", "Votre optimisme ouvre de nouvelles perspectives.",
        "En amour, la liberté et la complicité vont de pair.", "Un projet à l'étranger ou lointain avance.",
        "Votre franchise est appréciée par un collègue.", "Une idée audacieuse mérite d'être tentée.",
        "Côté finances, un pari raisonné peut payer.", "Une discussion enrichissante élargit votre vision.",
        "Une sortie en plein air vous redonne de l'élan.", "Votre humour fédère les énergies.",
        "Un apprentissage nouveau vous passionne.",
    ],
    "Capricorne": [
        "Votre sérieux inspire le respect.", "Un objectif professionnel se précise enfin.",
        "En amour, un engagement sincère se renforce.", "Votre sens des responsabilités est remarqué.",
        "Un effort fourni depuis longtemps commence à payer.", "Une organisation rigoureuse vous donne une longueur d'avance.",
        "Côté finances, la prudence est votre meilleure alliée.", "Une personne d'expérience vous offre un bon conseil.",
        "Vous construisez quelque chose de solide, brique après brique.", "Une soirée au calme vous fait le plus grand bien.",
        "Votre persévérance fait taire les doutes.",
    ],
    "Verseau": [
        "Votre originalité fait mouche aujourd'hui.", "Une idée innovante retient l'attention.",
        "En amour, l'amitié et la complicité intellectuelle priment.", "Un projet collectif vous enthousiasme.",
        "Votre indépendance d'esprit ouvre une nouvelle voie.", "Une rencontre inattendue stimule votre imagination.",
        "Côté travail, la technologie ou un outil nouveau vous facilite la vie.", "Une cause qui vous tient à cœur mobilise votre énergie.",
        "Une discussion décalée vous fait aimer la journée.", "Vous sortez des sentiers battus avec succès.",
        "Un ami vous apporte un éclairage précieux.",
    ],
    "Poissons": [
        "Votre imagination est une source d'inspiration.", "Votre intuition capte ce que les mots taisent.",
        "En amour, un moment de rêverie partagée vous rapproche.", "Un élan artistique ou créatif vous comble.",
        "Votre empathie réconforte une personne proche.", "Un rêve ou une idée floue gagne en clarté.",
        "Côté travail, une approche douce se révèle efficace.", "Un moment de calme près de l'eau ou en musique vous ressource.",
        "Votre sensibilité guide une bonne décision.", "Une aide discrète vous arrive au bon moment.",
        "Vous lâchez prise sur un souci qui vous pesait.",
    ],
}

CONSEIL = [
    "Attention à la dispersion.", "Évitez de vous laisser envahir par les doutes.", "Pensez à vous accorder une vraie pause.",
    "Attention à ne pas vous précipiter.", "Écoutez votre corps, il vous parle.", "Évitez les discussions inutiles ce soir.",
    "Gardez un peu de souplesse face aux imprévus.", "Prenez le temps de bien lire avant de signer ou de promettre.",
    "Attention à la fatigue en fin de journée.", "Ne remettez pas à demain un petit geste important.",
    "Évitez les dépenses impulsives.", "Pensez à dire merci, cela change tout.",
    "Attention aux paroles lancées trop vite.", "Laissez de la place à l'improvisation.",
    "Évitez de comparer votre chemin à celui des autres.", "Prenez un moment pour respirer profondément.",
    "Ne vous chargez pas des soucis des autres.", "Attention à l'excès de perfectionnisme.",
    "Faites confiance à votre première impression.", "Pensez à hydrater votre corps et votre esprit.",
    "Évitez de trop vous disperser sur les écrans.", "Mettez un peu de douceur dans vos échanges.",
    "Attention à ne pas tout vouloir contrôler.", "Osez dire non quand il le faut.",
    "Gardez un œil sur votre budget.", "Profitez d'un instant simple sans culpabiliser.",
    "Attention à l'impatience, elle brouille les pistes.", "Évitez de vous isoler trop longtemps.",
    "Accordez-vous une petite récompense.", "Terminez la journée sur une pensée positive.",
]

assert len(AMBIANCE) == len(CONSEIL) == 30 and all(len(v) == 11 for v in PAR_SIGNE.values())


def horoscope(i_signe, jour: datetime.date):
    """Texte du signe n° i_signe (0 = Bélier) pour la date donnée."""
    n = jour.toordinal()
    a = AMBIANCE[(n + 5 * i_signe) % 30]
    b = PAR_SIGNE[SIGNES[i_signe]][(n + 3 * i_signe) % 11]
    c = CONSEIL[(7 * n + 11 * i_signe) % 30]
    return f"{a} {b} {c}"
