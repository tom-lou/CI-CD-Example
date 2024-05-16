from fastapi import FastAPI, HTTPException
import base64
import os

from mylib import functions, criterias

app = FastAPI()

@app.post('/process_base64')
async def process_base64(data: dict):
    try:
        base64_data = data.get("base64_data")
        if not base64_data:
            raise HTTPException(status_code=400, detail="Le paramètre 'base64_data' est manquant dans le dictionnaire.")

        # Conversion de la base64 en données binaires
        binary_data = base64.b64decode(base64_data, validate=True)

        # Détection du type de fichier
        file_extension = detect_file_type(binary_data)

        # Variables de contrôle
        found_date = False
        found_ref_archives = False
        found_non_soumis = False
        found_finess = False
        found_adherant = False
        found_date_compare = False
        found_count_ref = False
        found_mat_med = False
        found_taux = False

        if file_extension == 'pdf':
            with open('output.pdf', 'wb') as pdf_out:
                pdf_out.write(binary_data)

            pdf_file = 'output.pdf'
            pages = None  # Traiter toutes les pages
            png_files = functions.pdf2img(pdf_file, pages)

            for png_file in png_files:
                print("---Traitement de la page : " + os.path.basename(png_file) + "...")
                png_text = functions.img2text(png_file)
                png_text_list = functions.img2textlist(png_file)

                found_taux = criterias.taux_compare(png_text_list)
                found_date = criterias.dateferiee(png_text)
                found_ref_archives = criterias.refarchivesfaux(png_text)
                found_non_soumis = criterias.rononsoumis(png_text)
                found_finess = criterias.finessfaux(png_text)
                found_date_compare = criterias.date_compare(png_text_list)
                found_count_ref = criterias.count_ref(png_text_list)
                found_adherant = criterias.adherentssuspicieux(png_text)
                found_mat_med = criterias.medical_materiel(png_text)

                # Si un élément est trouvé, on arrête le script instantanément
                if found_date or found_ref_archives or found_non_soumis or found_finess or \
                        found_date_compare or found_count_ref or found_adherant or found_mat_med or found_taux:
                    break

        elif file_extension in ['jpg', 'jpeg', 'png']:
            # Traitement de l'image directement
            png_text = functions.img2text(binary_data)
            png_text_list = functions.img2textlist(binary_data)

            found_date = criterias.dateferiee(png_text)
            found_ref_archives = criterias.refarchivesfaux(png_text)
            found_non_soumis = criterias.rononsoumis(png_text)
            found_finess = criterias.finessfaux(png_text)
            found_date_compare = criterias.date_compare(png_text_list)
            found_count_ref = criterias.count_ref(png_text_list)
            found_adherant = criterias.adherentssuspicieux(png_text)
            found_mat_med = criterias.medical_materiel(png_text)
            found_taux = criterias.taux_compare(png_text_list)

        else:
            raise HTTPException(status_code=400, detail="Format de fichier non supporté")

        result_dict = {
            "date_feriee_trouvee": found_date,
            "reference_archivage_trouvee": found_ref_archives,
            "rononsoumis_trouvee": found_non_soumis,
            "finess_faux_trouvee": found_finess,
            "adherant_suspicieux_trouvee": found_adherant,
            "date_superieur_trouver": found_date_compare,
            "ref_superieur_trouver": found_count_ref,
            "materiel_medical_trouvee": found_mat_med,
            "taux_trouvee": found_taux
        }

        return result_dict

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

def detect_file_type(data):
    # Déterminer le type de fichier en fonction de l'en-tête
    if data.startswith(b'%PDF'):
        return 'pdf'
    elif data.startswith(b'\xFF\xD8'):
        return 'jpeg'
    elif data.startswith(b'\x89PNG'):
        return 'png'
    else:
        raise HTTPException(status_code=400, detail="Format de fichier non supporté")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
