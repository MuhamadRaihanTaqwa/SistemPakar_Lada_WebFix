from flask import Flask, render_template, request
import json

app = Flask(__name__)

# Fungsi combine CF
def combine_cf(cf1, cf2):
    return cf1 + cf2 * (1 - cf1)

# Load rules
with open("rules.json", "r", encoding="utf-8") as f:
    rules = json.load(f)
    # --- Informasi penyakit dan solusinya ---
penyakit_info = {
    "Busuk Akar": {
        "deskripsi": "Penyakit ini disebabkan oleh jamur Phytophthora capsici yang menyerang akar sehingga tanaman layu dan mati.",
        "solusi": "Gunakan fungisida berbahan aktif metalaksil, perbaiki drainase, dan hindari kelembapan tinggi di sekitar akar."
    },
    "Busuk Pangkal": {
        "deskripsi": "Penyakit yang disebabkan oleh jamur Fusarium oxysporum yang menyerang pangkal batang dan menyebabkan jaringan busuk.",
        "solusi": "Cabut dan musnahkan tanaman terinfeksi, gunakan tanah steril, dan tambahkan Trichoderma sebagai agen hayati."
    },
    "Kuning Daun": {
        "deskripsi": "Gejala daun menguning akibat kekurangan unsur hara nitrogen atau infeksi nematoda pada akar.",
        "solusi": "Tambahkan pupuk nitrogen, perbaiki aerasi tanah, dan lakukan rotasi tanaman dengan jenis bukan lada."
    },
    "Kerdil Keriting": {
        "deskripsi": "Disebabkan oleh serangan virus yang ditularkan oleh kutu daun, menyebabkan daun keriting dan tanaman kerdil.",
        "solusi": "Semprot insektisida untuk mengendalikan vektor, dan gunakan bibit bebas virus."
    },
    "Ganggang Pirang": {
        "deskripsi": "Serangan alga hijau keemasan yang menyebabkan pertumbuhan tanaman terhambat.",
        "solusi": "Kurangi kelembapan dan tingkatkan sirkulasi udara, serta lakukan pemangkasan rutin."
    }
}


# Ambil semua gejala
possible_facts = sorted({g for r in rules for g in r["if"]})

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        selected = request.form.getlist("gejala")
        known = {s: 1.0 for s in selected}
        fired = True
        fired_rules = set()

        while fired:
            fired = False
            for r in rules:
                if r["id"] in fired_rules:
                    continue
                prem = r["if"]
                matched = [p for p in prem if p in known]
                if not matched:
                    continue
                ratio = len(matched) / len(prem)
                premise_cf = min(known[p] for p in matched)
                weighted_cf = premise_cf * ratio
                inferred_cf = weighted_cf * r.get("cf", 1.0)
                conclusion = r["then"]
                if conclusion in known:
                    known[conclusion] = combine_cf(known[conclusion], inferred_cf)
                else:
                    known[conclusion] = inferred_cf
                fired_rules.add(r["id"])
                fired = True

        # --- hasil diagnosa ---
        hasil = [
            {"penyakit": k.replace("_", " ").title(), "cf": v * 100}
            for k, v in known.items() if k not in possible_facts
        ]
        hasil.sort(key=lambda x: x["cf"], reverse=True)

        # --- tambahkan deskripsi & solusi ---
        for h in hasil:
            nama = h["penyakit"]
            info = penyakit_info.get(
                nama,
                {
                    "deskripsi": "Informasi belum tersedia.",
                    "solusi": "Belum ada solusi yang direkomendasikan."
                }
            )
            h["deskripsi"] = info["deskripsi"]
            h["solusi"] = info["solusi"]

        # --- tambahkan kesimpulan ---
        if hasil:
            penyakit_teratas = hasil[0]
            kesimpulan = (
                f"Berdasarkan gejala yang Anda pilih, kemungkinan terbesar tanaman lada "
                f"mengalami penyakit {penyakit_teratas['penyakit']} "
                f"dengan tingkat keyakinan {penyakit_teratas['cf']:.1f}%. "
                f"{penyakit_teratas['deskripsi']} "
                f"Disarankan untuk {penyakit_teratas['solusi']}"
            )
        else:
            kesimpulan = "Tidak ditemukan penyakit yang cocok berdasarkan gejala yang dipilih."

        # --- label dan nilai untuk Chart.js ---
        labels = [h["penyakit"] for h in hasil]
        values = [round(h["cf"], 1) for h in hasil]

        # --- render hasil ke halaman result.html ---
        return render_template(
            "result.html",
            hasil=hasil,
            selected=selected,
            labels=labels,
            values=values,
            kesimpulan=kesimpulan
        )

    # --- jika GET, tampilkan halaman awal ---
    return render_template("index.html", gejala=possible_facts)




if __name__ == "__main__":
    app.run(debug=True, port=5000)
