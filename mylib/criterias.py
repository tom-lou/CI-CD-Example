import re 
import pandas as pd
from . import constants,paths
from datetime import date
from jours_feries_france import JoursFeries 
from dateutil.relativedelta import relativedelta 
# from autocorrect import Speller
import cv2 
import argparse
# from imutils import paths
from datetime import datetime
import numpy as np 


def replace_last_9(text):
    index_last_9 = text.rfind("9")
    if index_last_9 != -1:  # verifier si un "9" a ete rouver
        return text[:index_last_9] + text[index_last_9:].replace("9", "", 1)
    else:
        return text

def taux_compare(pngText):
    result_list = []
    regex = re.compile(r"\d{2}[ ]?[%9]|(100[ ]?%)")
    for pourcentage_index, pourcentage in enumerate(pngText):

        if re.match(regex, pourcentage):
            if pourcentage.endswith("%"):
                pourcentage = pourcentage.replace("%", "")
                print(f"Pourcentage trouvé à l'index {pourcentage_index}: {pourcentage}")
            elif pourcentage.endswith("9"):
                pourcentage = replace_last_9(pourcentage)
                print(f"Pourcentage trouvé à l'index {pourcentage_index}: {pourcentage}")
                
            if pourcentage_index > 0 and pourcentage_index < len(pngText) - 1:
                print(f"Pourcentage trouvé à l'index {pourcentage_index}: {pourcentage}")
                mot_avant = pngText[pourcentage_index - 1].replace(",", ".")
                mot_apres = pngText[pourcentage_index + 1].replace(",", ".")
                print("Mot précédent:", mot_avant)
                print("Mot suivant:", mot_apres)

                try:
                    res = float(mot_avant.replace(" ", ".")) * float(pourcentage) / 100
                    print("Le résultat est :", round(res, 3))

                    if round(float(res), 2) == float(mot_apres):
                        print("C'est ok")
                    else:
                        result_list.append(res)
                        print("Pas ok")
                except ValueError:
                    print("Erreur de conversion en float")

            else:
                print("Pas de mot précédent ou suivant")

    if result_list:
        return True
    else:
        return False





def dateferiee(pngText):
    # On récupère la liste des dates dans le texte
    dateList = re.findall(r'([0-2]{1}[0-9]{1})[/-](1[0-2]{1}|0[1-9]{1})[/-]([0-9]{2,4})', pngText)
    dateList = list(dict.fromkeys(dateList))
    # On récupère la liste des indices sur Alsace-Moselle dans le texte
    cpList = re.findall(r'[5-6]7\d{3}', pngText)
    cityList = re.findall(r'[a|A]lsace|[m|M]oselle', pngText)

    # On initialise le résultat
    result = False

    for dateSplit in dateList :
        dateFormat = date(int(dateSplit[2]), int(dateSplit[1]), int(dateSplit[0]))

        # Si la date est inférieure à la durée maximale de remboursement,        
        if relativedelta(date.today(), dateFormat).years < constants.MAX_REFUND_YEARS :

            # Si on est en Alsace-Moselle
            if len(cpList) > 0 or len(cityList) > 0 :
                if JoursFeries.is_bank_holiday(dateFormat, zone="Alsace-Moselle") :
                    result = True
                    break
            else :
                # Si c'est un jour férié en Métropole, on suspecte une fraude
                if JoursFeries.is_bank_holiday(dateFormat, zone="Métropole") :
                    result = True
                    break
    return result



def medical_materiel(pngText):
    result_list = []

    # RegEx pour détecter les mots-clés médicaux et les montants
    matches = re.findall(r'(apnée|apnee|APNEE|PERFUSION|perfusion|LOCATION|location|PPC|ppc)', pngText)
    detect_montant = re.findall(r'(?i)(?:part mutuelle|net [àa] payer|a[.]?[ ]?m[.]?[ ]?c|Votre d[ûu]|ticket mod[ée]rateur)\s*:? ?(\d+[ ]?[.,][ ]?\d+)', pngText)

    if matches: 
        if detect_montant:
            print("Les montants détectés sont :", detect_montant)

            for montant in detect_montant:
                #supprimer les espaces
                montant = montant.replace(" ", "")
                montant_float = float(montant.replace(",", "."))
                print("Le montant mutuelle détecté est :", montant)

                if montant_float > 150.00:
                    result_list.append(montant)
                    print("Le montant est supérieur à 150 EUR")
                    break
                else:
                    print("Le prix est inférieur à 150 EUR")
        else:
            print("Aucun montant trouvé")

        print("Facture matériel médical trouvée")

    if result_list:
        return True
    else:
        return False



def rononsoumis(pngText):
    # On récupère les indices relatifs au régime obligatoire
    regimeList = re.findall(r'[r|R][é|e]gime [o|O]bligatoire|[R|r][O|o]|REGIME OBLIGATOIRE', pngText)
    # print(regimeList)
    # On recherche les indices relatifs aux prestations non soumis au Régime obligatoire
    sansRoList = re.findall("|".join(constants.NONRO_PRESTA), pngText)

    if "" in sansRoList:
        sansRoList=[]
    
    # print(sansRoList)

    # Si l'on trouve
    if len(regimeList) > 0 and len(sansRoList) > 0 :
        return True
    else :
        return False
    

def finessfaux(pngText):
    # On récupère la liste des Numéros finess des adhérents suspects
    data = pd.read_excel(r'C:\Users\pierrontl\OneDrive - GIE SIMA\Documents\GitHub\Fraude\code_Tom\docker\v2\app2\surveillance.xlsx', sheet_name="finess")
    finessList = data["NUMERO FINESS"].tolist()
    # print(finessList)
    # print("|".join(str(s) for s in finessList))
    # On recherche les indices relatifs à la présence d'un numéro finess dans la page
    resultList = re.findall(r"|".join(str(s) for s in finessList), pngText)
    
    print("la result liste est :",resultList)
    if len(resultList) > 0 :
        return True
    else :
         return False



def adherentssuspicieux(pngText):
    # On récupère la liste des noms des adhérents suspects
    data = pd.read_excel(r'C:\Users\pierrontl\OneDrive - GIE SIMA\Documents\GitHub\Fraude\code_Tom\docker\v2\app2\surveillance.xlsx', sheet_name="Adhérents")
    usersList = data["NOM Complet"].tolist()
    # print(usersList)
    resultList = re.findall("|".join(usersList).upper(), pngText.upper())
    # print(resultList)

    if len(resultList) > 0 :
        return True
    else :
         return False


def compare(date_simple_str, date_reglement_str):
    # convertir objet str en datetime
    date_simple = datetime.strptime(date_simple_str, "%d/%m/%Y")
    date_reglement = datetime.strptime(date_reglement_str, "%d/%m/%Y")

    # Comparer les dates
    if date_simple > date_reglement:
        print(f"{date_simple_str} est supérieure à {date_reglement_str}")
        return True
    else:
        print(f"{date_simple_str} n'est pas supérieure à {date_reglement_str}")
        return False



def extract_reglement_date(value):
    regex_regle = r'réglé le (\d{1,2}/\d{1,2}/\d{4})'
    regex_destinataire = r'(\d{1,2}/\d{1,2}/\d{4}) au destinataire'
    regex_euro = r'(\d{1,2}/\d{1,2}/\d{4}) : (\d+(?:,\d{1,2})?) euro' # Ajouter le faite qu'il peut avoir un montant en euro
    match_regle = re.search(regex_regle, value)
    match_destinataire =re.search(regex_destinataire, value)
    match_euro = re.search(regex_euro, value)

    if match_regle:
        return match_regle.group(1)
    
    elif match_destinataire:
        return match_destinataire.group(1)
    
    elif match_euro:
        return match_euro.group(1)
    
    return None



def isDateSimple(value):
    regex_simple = r'\b(?:[0-3]?[0-9][/|-](?:1[0-2]|0?[1-9])[/|-](?:\d{2}|\d{4}))\b'
    return re.match(regex_simple, value)



def date_compare(pngText):
    myBlocs = []
    currentBloc = []
    started = False
    for value in pngText:
        if not started:
            currentBloc = []
            started = True

        if isDateSimple(value) and "au destinataire" not in value:  # Ajout de la condition ici
            currentBloc.append(value)

        reglement_date = extract_reglement_date(value)
        if reglement_date:
            currentBloc.append(reglement_date)
            myBlocs.append(currentBloc)
            currentBloc = []

    date_superieur_trouver = False
    for block in myBlocs:
        date_reglement = block[-1]
        print("date de règlement :", date_reglement)
        date_normales = block[:-1]
        print("date simple :", date_normales)

        for date in date_normales:
            result = compare(date, date_reglement)
            if result:
                date_superieur_trouver = True
                break
        if date_superieur_trouver:
            break
    return date_superieur_trouver


def count_ref(pngText):
    result = False

    for text in pngText:
        pattern = re.compile(r'r[é|ë|è]f (\d+)[ ]?[ ][ ]?[ ]?(\d+)')
        matches = pattern.findall(text)

        if matches:
            for match in matches:
                group_variable = ''.join(match)
                print("result group variable:", group_variable)

                if len(group_variable) > 17:
                    print("la reference d'archivage est superieur a 17")
                    result = True
                else:
                    print("la reference d'archivage n'est pas superieur a 17")
                    result = False

    return result



def refarchivesfaux(pngText):
    rechmot = re.findall(r'CPAM|ensemble|Agir', pngText)
    
    if 'CPAM' in rechmot or 'ensemble' in rechmot or 'Agir' in rechmot:
        refList = re.findall(r'\d{4}[ ]?[  ]?[   ]?(\d{2})(\d{3})\d{8}', pngText)
        print("Références d'archivage trouvées :", refList)

        if not refList:
            return False
        else:
            dateList = re.findall(r'([0-2]{1}[0-9]{1})[/-](1[0-2]{1}|0[1-9]{1})[/-]([0-9]{2,4})', pngText)
            print("Dates trouvées :", dateList)

            for refSplit in refList:
                currentResult = False
                # Pour chaque date récupérée
                for dateSplit in dateList:
                    dateFormat = date(int(dateSplit[2]), int(dateSplit[1]), int(dateSplit[0]))
                    dateCompare = date(int(dateSplit[2]), 1, 1)
                    dateDelta = dateFormat - dateCompare

                    # On vérifie que l'année correspond
                    if dateSplit[2][-2:] == refSplit[0]:
                        # On vérifie que le nombre de jours correspond
                        if int(refSplit[1]) - constants.REF_AGE_DELTA <= int(dateDelta.days) <= int(refSplit[1]) + constants.REF_AGE_DELTA:
                            currentResult = True
                            break

                if not currentResult:
                    print("------Une fausse référence d'archivage a été trouvée !")
                    return True

            return False
    else:
        return False