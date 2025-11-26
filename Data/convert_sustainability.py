import pandas as pd
import os

def transform_data():
    print("--- Veri Dönüşümü Başlıyor ---")
    
    # 1. Dosyaları Oku
    if not os.path.exists("sustainability.csv") or not os.path.exists("countries.csv"):
        print("HATA: 'sustainability.csv' veya 'countries.csv' dosyası bulunamadı!")
        return

    df_raw = pd.read_csv("sustainability.csv")
    df_countries = pd.read_csv("countries.csv")
    
    print(f"Ham Veri Yüklendi: {len(df_raw)} satır")

    # 2. İndikatör Haritası
    indicator_map = {
        "People using  safely managed drinking water services  % of population 2017": (1, 2017),
        "People using  safely managed sanitation services  % of population 2017": (2, 2017),
        "Access to electricity  % of population 2017": (3, 2017),
        "Renewable energy consumption  % of total final energy consumption 2015": (4, 2015),
        "Expenditures for R&D  % of GDP 2015": (5, 2015),
        "Urban population living in slums  % of urban population 2014": (6, 2014),
        "Ambient PM2.5 air pollution mean annual exposure micrograms per cubic meter 2016": (7, 2016),
        "Adjusted net savings  % of GNI 2017": (8, 2017),
        "Carbon dioxide emissions per capita metric tons 2014": (9, 2014),
        "Nationally protected terrestrial and marine areas  % of total territorial area 2018": (10, 2018),
        "Intentional homicides Combined source estimates per 100,000 people 2015": (11, 2015),
        "Internet use Individuals using the Internet % of population 2017": (12, 2017)
    }

    # 3. İSİM DÜZELTME HARİTASI (Güncellendi ✅)
    country_corrections = {
        # Hata verenler ve Çözümleri:
        "Bosnia and Herzegovina": "Bosnia And Herzegovina", # 'And' büyük harf
        "Congo, Dem. Rep.": "Congo (Democratic Republic Of The)",
        "Cote d'Ivoire": "Côte D'Ivoire", # Şapkalı harfler
        "Curacao": "Curaçao",
        "Guinea-Bissau": "Guinea Bissau", # Tire yok
        "Micronesia, Fed. Sts.": "Micronesia (Federated States of)",
        "St. Martin (French part)": "Saint Martin (French part)",
        "West Bank and Gaza": "Palestine, State of", # Filistin verisi
        
        # Önceki düzeltmeler (Devam ediyor)
        "Bahamas, The": "Bahamas",
        "Egypt, Arab Rep.": "Egypt",
        "Gambia, The": "Gambia",
        "Iran, Islamic Rep.": "Iran",
        "Korea, Rep.": "South Korea",
        "Kyrgyz Republic": "Kyrgyzstan",
        "Lao PDR": "Laos",
        "Russian Federation": "Russia",
        "Slovak Republic": "Slovakia",
        "Syrian Arab Republic": "Syria",
        "Venezuela, RB": "Venezuela",
        "Yemen, Rep.": "Yemen",
        "Congo, Rep.": "Congo",
        "St. Kitts and Nevis": "Saint Kitts and Nevis",
        "St. Lucia": "Saint Lucia",
        "St. Vincent and the Grenadines": "Saint Vincent and the Grenadines",
        "Hong Kong SAR, China": "Hong Kong",
        "Macao SAR, China": "Macao",
        "North Macedonia": "Macedonia"
    }

    output_rows = []

    # 4. Dönüşüm Döngüsü
    for index, row in df_raw.iterrows():
        country_name = row['Country']
        
        # İsim düzeltme
        if country_name in country_corrections:
            country_name = country_corrections[country_name]
        
        # Eşleştirme
        country_match = df_countries[df_countries['country_name'] == country_name]
        
        if not country_match.empty:
            country_id = country_match.iloc[0]['country_id']
            
            for col_name, (ind_id, year) in indicator_map.items():
                if col_name in row:
                    value = row[col_name]
                    if pd.notna(value) and str(value).strip() != "":
                        output_rows.append({
                            'country_id': country_id,
                            'sus_indicator_id': ind_id,
                            'year': year,
                            'indicator_value': value,
                            'source_note': "WDI Data"
                        })
        else:
            # Buraya düşenler countries.csv'de HİÇ YOK demektir.
            # North Korea, Kosovo ve Channel Islands veritabanında olmadığı için atlanacak.
            print(f"Uyarı: '{row['Country']}' (Aranan: {country_name}) veritabanında yok.")

    # 5. Kaydet
    if output_rows:
        df_out = pd.DataFrame(output_rows)
        df_out.to_csv("sustainability_data.csv", index=False)
        print(f"--- Başarılı! 'sustainability_data.csv' oluşturuldu ({len(df_out)} satır) ---")
    else:
        print("HATA: Hiçbir veri dönüştürülemedi.")

if __name__ == "__main__":
    transform_data()