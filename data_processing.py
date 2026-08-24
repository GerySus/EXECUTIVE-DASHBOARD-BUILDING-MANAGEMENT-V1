"""Fetch the Agrinas Google Sheet and turn it into plain dict/list data that
the Flask templates and JS charts can consume directly (no NiceGUI).
"""
import io
import time

import pandas as pd
import requests

SHEET_ID = "1cG9Fk0lOsEXtz1ECabe7uaL7gtdDMTnCJesFcBaan8Y"
GID = "1762202601"            # EXECUTIVE DASHBOARD
DATA_GID = "1762202602"       # _Dashboard Data (sumber chart & tabel)
REGIONAL_GID = "613278276"    # List Pekerjaan Regional (sumber peta lokasi)
FURNITURE_GID = "107274767"   # List Furniture Regional (sumber peta lokasi)


def sheet_url(gid):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"


def load(url):
    """Fetch a public Sheet tab as a headerless DataFrame.

    Uses requests (honors http_proxy/https_proxy env vars set by
    PythonAnywhere's outbound proxy) instead of letting pandas open the URL
    itself, so a network failure degrades to an empty frame instead of
    crashing the whole page.
    """
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return pd.read_csv(io.StringIO(resp.text), header=None)
    except Exception:
        return pd.DataFrame()


def cell(frame, r, c, default=""):
    try:
        v = frame.iat[r, c]
        if pd.isna(v):
            return default
        s = str(v).strip()
        return s if s else default
    except Exception:
        return default


def to_int(s, default=0):
    try:
        return int(str(s).replace(".", "").replace(",", "").strip())
    except Exception:
        return default


def to_rupiah_int(s, default=0):
    try:
        cleaned = str(s).replace("Rp", "").strip().split(",")[0].replace(".", "")
        return int(cleaned)
    except Exception:
        return default


def format_rupiah_short(value):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    sign = "-" if v < 0 else ""
    v = abs(v)
    if v >= 1_000_000_000_000:
        num, suffix = v / 1_000_000_000_000, "T"
    elif v >= 1_000_000_000:
        num, suffix = v / 1_000_000_000, "M"
    elif v >= 1_000_000:
        num, suffix = v / 1_000_000, "Jt"
    else:
        return f"Rp{sign}{v:,.0f}".replace(",", ".")
    text = f"{num:.1f}".rstrip("0").rstrip(".").replace(".", ",")
    return f"Rp{sign}{text} {suffix}"


STATUS_LEGEND = [
    ("Selesai", "#22D3A5"),
    ("Rehabilitasi Ringan", "#38BDF8"),
    ("Dalam Proses", "#F5A623"),
    ("Perlu Tindak Lanjut", "#F87171"),
    ("Belum Ada Update", "#8895A7"),
]
STATUS_COLORS = dict(STATUS_LEGEND)

REGIONAL_COORDS = [
    (3.5952, 98.6722),     # 1  Sumut/Aceh - Medan
    (0.5071, 101.4478),    # 2  Riau 1 (Ex.Duta Palma) - Pekanbaru
    (1.6265, 101.4360),    # 3  Riau 2 (PKH) + Riau 3 (PKH)
    (0.3021, 102.4207),    # 4  Riau 4 (Ex.Torganda 2)
    (-1.6101, 103.6131),   # 5  Sumbar/Sumsel/Babel/Jambi - Jambi
    (-0.0263, 109.3425),   # 6  Kalbar - Pontianak
    (-1.2379, 116.8529),   # 7  Kalsel, Kaltim, Kaltara - Balikpapan
    (-2.5330, 112.9500),   # 8  Kalteng 1 (PKH) - Sampit
    (-2.2090, 113.9213),   # 9  Kalteng 2 (PKH) - Palangkaraya
    (-5.1477, 119.4327),   # 10 Sulawesi Selatan - Makassar
    (-2.5330, 140.7181),   # 11 Papua - Jayapura
]

SPARKS = {
    'cyan': [5, 8, 4, 9, 6, 7, 4, 10, 6, 8],
    'green': [3, 7, 5, 8, 4, 9, 5, 6, 8, 5],
    'purple': [7, 4, 9, 5, 8, 4, 10, 6, 5, 9],
    'orange': [4, 9, 5, 7, 3, 8, 6, 9, 4, 7],
    'teal': [6, 4, 8, 3, 7, 5, 9, 4, 8, 6],
}
BADGE_MAP = {'TINGGI': 'badge-tinggi', 'SEDANG': 'badge-sedang', 'RENDAH': 'badge-rendah'}


def classify_status(text):
    t = text.lower()
    if "selesai" in t:
        return "Selesai"
    if "ringan" in t:
        return "Rehabilitasi Ringan"
    if "menunggu" in t or "proses" in t or "progres" in t:
        return "Dalam Proses"
    if "rencana" in t or "membutuhkan" in t or "sementara" in t:
        return "Perlu Tindak Lanjut"
    return "Belum Ada Update"


def parse_kota(raw):
    if not raw:
        return "-"
    kota = raw.split(">")[0].strip()
    if kota.startswith("http"):
        return "-"
    return kota


def _echart_line(color, spark):
    return {
        'grid': {'left': 3, 'right': 3, 'top': 5, 'bottom': 3},
        'xAxis': {'show': False, 'type': 'category', 'data': list(range(len(spark))), 'boundaryGap': False},
        'yAxis': {'show': False, 'type': 'value', 'scale': True},
        'tooltip': {
            'show': True, 'trigger': 'axis', 'appendToBody': True,
            'backgroundColor': '#0E2038', 'borderColor': 'rgba(255,255,255,.15)', 'borderWidth': 1,
            'textStyle': {'color': '#EAF6FF', 'fontSize': 11},
            'axisPointer': {'type': 'line', 'lineStyle': {'color': color, 'width': 1, 'opacity': 0.5}},
            'formatter': '{c}', 'padding': [4, 8],
        },
        'series': [{
            'type': 'line', 'data': spark, 'smooth': False, 'showSymbol': True,
            'symbol': 'circle', 'symbolSize': 5,
            'lineStyle': {'color': color, 'width': 2, 'shadowColor': color, 'shadowBlur': 6},
            'itemStyle': {'color': color, 'borderColor': '#0B1220', 'borderWidth': 1},
            'areaStyle': {
                'opacity': 1,
                'color': {'type': 'linear', 'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                          'colorStops': [{'offset': 0, 'color': f'{color}B3'},
                                         {'offset': 1, 'color': f'{color}26'}]},
            },
        }],
    }


def _echart_completed_pie(pekerjaan_selesai, belum_selesai, center_value):
    return {
        'tooltip': {'trigger': 'item', 'backgroundColor': '#0E2038',
                    'borderColor': 'rgba(255,255,255,.15)', 'borderWidth': 1,
                    'textStyle': {'color': '#EAF6FF', 'fontSize': 12},
                    'formatter': '{b}: {c} ({d}%)'},
        'series': [{
            'type': 'pie', 'radius': ['64%', '88%'], 'center': ['50%', '50%'],
            'label': {'show': False},
            'emphasis': {'scale': True, 'scaleSize': 6,
                         'itemStyle': {'shadowBlur': 18, 'shadowColor': 'rgba(0,0,0,.5)'}},
            'data': [
                {'value': pekerjaan_selesai, 'name': 'Selesai', 'itemStyle': {'color': '#F87171'}},
                {'value': belum_selesai, 'name': 'Belum Selesai', 'itemStyle': {'color': '#F5A623'}},
            ],
        }],
        'graphic': [{
            'type': 'group', 'left': 'center', 'top': 'center',
            'children': [
                {'type': 'text', 'style': {'text': center_value, 'textAlign': 'center', 'fontSize': 23,
                                            'fontWeight': 800, 'fill': '#fff'}, 'left': 'center', 'top': -15},
                {'type': 'text', 'style': {'text': 'Selesai', 'textAlign': 'center', 'fontSize': 12,
                                            'fill': '#8FB4CC'}, 'left': 'center', 'top': 13},
            ],
        }],
    }


def _echart_delivery_bar(delivery_perf, full=False):
    return {
        'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'},
                    'backgroundColor': '#0E2038', 'borderColor': 'rgba(255,255,255,.15)',
                    'borderWidth': 1, 'textStyle': {'color': '#EAF6FF', 'fontSize': 12},
                    'formatter': None if full else '{b}<br/>Jumlah Pekerjaan: <b>{c}</b>'},
        'grid': {'left': 50 if full else 40, 'right': 30 if full else 20,
                 'top': 30 if full else 20, 'bottom': 40 if full else 30},
        'xAxis': {'type': 'category', 'data': [d['name'] for d in delivery_perf],
                  'axisLine': {'lineStyle': {'color': '#2B4560'}},
                  'axisLabel': {'color': '#9FC7DE', 'fontSize': 12 if full else 11}},
        'yAxis': {'type': 'value', 'name': 'Jumlah Pekerjaan',
                  'nameTextStyle': {'color': '#6E8CA4', 'fontSize': 11 if full else 10},
                  'splitLine': {'lineStyle': {'color': 'rgba(255,255,255,.06)'}},
                  'axisLabel': {'color': '#9FC7DE', 'fontSize': 12 if full else 11}},
        'series': [{
            'type': 'bar', 'data': [d['value'] for d in delivery_perf],
            'barWidth': '38%' if full else '42%',
            'itemStyle': {
                'color': {'type': 'linear', 'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                          'colorStops': [{'offset': 0, 'color': '#7DD8FF'},
                                         {'offset': 1, 'color': '#0B6EC7'}]},
                'borderRadius': [8, 8, 0, 0] if full else [6, 6, 0, 0]},
            'emphasis': {'itemStyle': {
                'color': {'type': 'linear', 'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                          'colorStops': [{'offset': 0, 'color': '#B6ECFF'},
                                         {'offset': 1, 'color': '#38BDF8'}]},
                'shadowBlur': 14, 'shadowColor': 'rgba(56,189,248,.6)'}},
            'label': {'show': True, 'position': 'top', 'color': '#EAF6FF',
                      'fontWeight': 700, 'fontSize': 13 if full else None},
        }],
    }


def _echart_investment_bar(items, left=190):
    return {
        'grid': {'left': left, 'right': 55, 'top': 10, 'bottom': 30},
        'xAxis': {'type': 'value', 'name': 'Nilai Investasi',
                  'nameTextStyle': {'color': '#6E8CA4', 'fontSize': 9.5},
                  'axisLabel': {'show': False},
                  'splitLine': {'lineStyle': {'color': 'rgba(255,255,255,.06)'}}},
        'yAxis': {'type': 'category', 'inverse': True,
                  'data': [d['name'] for d in items],
                  'axisLabel': {'color': '#B9D4E8', 'fontSize': 9.5, 'width': left - 15, 'overflow': 'truncate'},
                  'axisLine': {'lineStyle': {'color': '#2B4560'}}},
        'series': [{
            'type': 'bar',
            'data': [{'value': d['value'], 'label': {'formatter': format_rupiah_short(d['value'])}} for d in items],
            'barWidth': '55%',
            'itemStyle': {
                'color': {'type': 'linear', 'x': 0, 'y': 0, 'x2': 1, 'y2': 0,
                          'colorStops': [{'offset': 0, 'color': '#0EA5E9'},
                                         {'offset': 1, 'color': '#22D3A5'}]},
                'borderRadius': [0, 6, 6, 0]},
            'emphasis': {'itemStyle': {
                'color': {'type': 'linear', 'x': 0, 'y': 0, 'x2': 1, 'y2': 0,
                          'colorStops': [{'offset': 0, 'color': '#5FC3FF'},
                                         {'offset': 1, 'color': '#5FE9C4'}]},
                'shadowBlur': 14, 'shadowColor': 'rgba(34,211,165,.6)'}},
            'label': {'show': True, 'position': 'right', 'color': '#EAF6FF', 'fontSize': 9.5},
        }],
    }


def build_dashboard_data():
    df = load(sheet_url(GID))
    df_data = load(sheet_url(DATA_GID))
    df_regional = load(sheet_url(REGIONAL_GID))
    df_furniture = load(sheet_url(FURNITURE_GID))

    # ---- KPI (baris 5=judul, 7=nilai, 9=subjudul) ----
    kpi_cols = [0, 5, 10, 15, 20]
    kpi_title = [cell(df, 5, c, t) for c, t in zip(
        kpi_cols, ["TOTAL PERMOHONAN", "PEKERJAAN SELESAI", "TINGKAT PENYELESAIAN", "NILAI INVESTASI", "LOKASI REGIONAL"])]
    kpi_value = [cell(df, 7, c, v) for c, v in zip(
        kpi_cols, ["61", "34", "55,74%", "Rp58.942.232.774,00", "11"])]
    kpi_sub = [cell(df, 9, c, s) for c, s in zip(kpi_cols, [
        "Seluruh pekerjaan terdaftar", "Realisasi pekerjaan", "Proyek reguler + investasi",
        "Portofolio kontrak", "Cakupan rehabilitasi"])]

    last_update = cell(df, 4, 3, "-")

    total_permohonan = to_int(kpi_value[0], 61)
    pekerjaan_selesai = to_int(kpi_value[1], 34)
    belum_selesai = max(total_permohonan - pekerjaan_selesai, 0)
    nilai_investasi_short = format_rupiah_short(to_rupiah_int(kpi_value[3], 0))

    kpi_icons = ['assignment', 'task_alt', 'insights', 'payments', 'location_on']
    kpi_colors = ['#00D4FF', '#22D3A5', '#A855F7', '#F5A623', '#38BDF8']
    kpi_sparks = [SPARKS['cyan'], SPARKS['green'], SPARKS['purple'], SPARKS['orange'], SPARKS['teal']]
    kpi_display_value = list(kpi_value)
    kpi_display_value[3] = nilai_investasi_short
    kpi_tooltip = [None, None, None, kpi_value[3], None]
    kpis = [
        {'title': kpi_title[i], 'value': kpi_display_value[i], 'sub': kpi_sub[i],
         'icon': kpi_icons[i], 'color': kpi_colors[i], 'tooltip': kpi_tooltip[i] or kpi_display_value[i],
         'chart_id': f'kpi-spark-{i}', 'chart_option': _echart_line(kpi_colors[i], kpi_sparks[i])}
        for i in range(5)
    ]

    # ---- Management Control Tower (baris 52 header, 53-55 data) ----
    tower_rows = []
    for r in range(53, 60):
        p = cell(df, r, 0)
        if not p:
            continue
        tower_rows.append({
            "p": p, "v": cell(df, r, 7, "-"), "risk": cell(df, r, 11, "-"), "aksi": cell(df, r, 16, "-"),
        })
    if not tower_rows:
        tower_rows = [
            {"p": "Pekerjaan portofolio belum selesai", "v": "27", "risk": "TINGGI",
             "aksi": "Lakukan review progres, hambatan, PIC, dan target penyelesaian"},
            {"p": "Pekerjaan dalam proses administrasi", "v": "16", "risk": "SEDANG",
             "aksi": "Tetapkan PIC dan batas waktu penyelesaian administrasi"},
            {"p": "Dokumen pekerjaan regional belum lengkap", "v": "8", "risk": "SEDANG",
             "aksi": "Validasi RAB, surat permohonan, dan kelengkapan pendukung"},
        ]
    risk_icon_map = {'TINGGI': ('priority_high', '#F87171'), 'SEDANG': ('warning', '#F5A623')}
    for r in tower_rows:
        r['badge_cls'] = BADGE_MAP.get(r['risk'].upper(), 'badge-sedang')
        r['risk_icon'], r['risk_icon_color'] = risk_icon_map.get(r['risk'].upper(), ('info', '#8895A7'))

    exec_signal = cell(df, 58, 0,
                        "Prioritas: percepatan penyelesaian pekerjaan, penuntasan administrasi, "
                        "dan konsistensi dokumen regional.")

    # ---- Portfolio Delivery Flow (baris 63 label, 65 nilai, 67 subjudul) ----
    flow_cols = [0, 6, 12, 18]
    flow_labels = [cell(df, 63, c, d) for c, d in zip(
        flow_cols, ["01  PENGAJUAN", "02  DISETUJUI", "03  SELESAI", "04  BELUM SELESAI"])]
    flow_values = [cell(df, 65, c, d) for c, d in zip(flow_cols, ["61", "51", "34", "27"])]
    flow_subs = [cell(df, 67, c, d) for c, d in zip(flow_cols, [
        "Seluruh portofolio", "Mendapat persetujuan", "Proyek + investasi", "Perlu pengendalian"])]
    flow_icons = ["assignment", "check_circle", "emoji_events", "schedule"]
    flow_colors = ["#38BDF8", "#A855F7", "#22D3A5", "#F87171"]
    flow_items = [
        {'label': flow_labels[i], 'value': flow_values[i], 'sub': flow_subs[i],
         'icon': flow_icons[i], 'color': flow_colors[i]}
        for i in range(4)
    ]

    # ---- Delivery Performance ----
    delivery_perf = []
    for r in range(1, 8):
        name = cell(df_data, r, 2)
        val = cell(df_data, r, 3)
        if not name:
            continue
        delivery_perf.append({"name": name, "value": to_int(val, 0)})
    if not delivery_perf:
        delivery_perf = [
            {"name": "Selesai", "value": 34}, {"name": "Administrasi", "value": 16},
            {"name": "SPMK", "value": 0}, {"name": "Lainnya", "value": 0},
        ]
    total_dp = sum(d['value'] for d in delivery_perf) or 1
    for d in delivery_perf:
        d['pct'] = round(d['value'] / total_dp * 100, 1)

    # ---- Investment Building ----
    investment_building_raw = []
    for r in range(1, 30):
        name = cell(df_data, r, 4)
        val = cell(df_data, r, 5)
        if not name:
            continue
        investment_building_raw.append({"name": name, "value": to_rupiah_int(val)})
    if not investment_building_raw:
        investment_building_raw = [
            {"name": "Pekerjaan Renovasi 10 Lantai", "value": 41520788158},
            {"name": "Pekerjaan Pemasangan SPKLU (EV Charging)", "value": 2080000000},
            {"name": "Pengadaan Infrastruktur Data & Jaringan", "value": 5738400000},
            {"name": "Pekerjaan Perbaikan Sistem HVAC", "value": 1598400000},
            {"name": "Pekerjaan CCTV", "value": 1800000000},
            {"name": "Pengadaan Jasa Service System Lift", "value": 1479852000},
            {"name": "Pekerjaan AC Tahap II", "value": 803255806},
            {"name": "Perbaikan Hydrant", "value": 178710000},
            {"name": "Perbaikan Pipa Header & Pompa", "value": 153180000},
            {"name": "Pembelian Alat-alat Lantai 6", "value": 143619923},
        ]
    investment_building_all = sorted(investment_building_raw, key=lambda d: d["value"], reverse=True)
    for d in investment_building_all:
        d['value_short'] = format_rupiah_short(d['value'])
    investment_building = investment_building_all[:10]

    # ---- Peta Sebaran Lokasi Regional ----
    regional_locations = []
    idx = 0
    for r in range(len(df_regional)):
        no_val = cell(df_regional, r, 1)
        if not no_val.isdigit():
            continue
        provinsi = cell(df_regional, r, 2, "-")
        kota = parse_kota(cell(df_regional, r, 3))
        proyek = cell(df_regional, r, 4, "-")
        dispo = cell(df_regional, r, 5)
        progres = cell(df_regional, r, 6)
        dokumen = cell(df_regional, r, 8, "-")
        keterangan = cell(df_regional, r, 9, "-")
        status = classify_status(" ".join([progres, dispo, keterangan]))
        lat, lng = REGIONAL_COORDS[idx] if idx < len(REGIONAL_COORDS) else (-2.5, 118.0)
        regional_locations.append({
            "no": no_val, "provinsi": provinsi, "kota": kota,
            "status": status, "color": STATUS_COLORS[status],
            "lat": lat, "lng": lng,
            "proyek": proyek, "dokumen": dokumen, "keterangan": keterangan,
            "furniture": "-", "furniture_status": "Belum Ada Update",
            "furniture_color": STATUS_COLORS["Belum Ada Update"],
        })
        idx += 1

    f_idx = 0
    for r in range(len(df_furniture)):
        no_val = cell(df_furniture, r, 1)
        if not no_val.isdigit() or f_idx >= len(regional_locations):
            continue
        furniture_desc = cell(df_furniture, r, 4, "-")
        f_dispo = cell(df_furniture, r, 5)
        f_progres = cell(df_furniture, r, 6)
        f_keterangan = cell(df_furniture, r, 8)
        if furniture_desc == "-":
            f_status = "Belum Ada Update"
        else:
            f_status = classify_status(" ".join([f_progres, f_dispo, f_keterangan]))
        regional_locations[f_idx]["furniture"] = furniture_desc
        regional_locations[f_idx]["furniture_status"] = f_status
        regional_locations[f_idx]["furniture_color"] = STATUS_COLORS[f_status]
        f_idx += 1

    if not regional_locations:
        fallback_meta = [
            ("1", "Sumut/Aceh", "MEDAN", "Dalam Proses"),
            ("2", "Riau 1 (Ex.Duta Palma)", "PEKANBARU", "Rehabilitasi Ringan"),
            ("3", "Riau 2 (PKH) + Riau 3 (PKH)", "-", "Perlu Tindak Lanjut"),
            ("4", "Riau 4 (Ex.Torganda 2)", "-", "Selesai"),
            ("5", "Sumbar/Sumsel/Babel/Jambi", "-", "Belum Ada Update"),
            ("6", "Kalbar", "PONTIANAK", "Dalam Proses"),
            ("7", "Kalsel, Kaltim, Kaltara", "BALIKPAPAN", "Rehabilitasi Ringan"),
            ("8", "Kalteng 1 (PKH)", "SAMPIT", "Selesai"),
            ("9", "Kalteng 2 (PKH)", "-", "Perlu Tindak Lanjut"),
            ("10", "Sulawesi Selatan", "MAKASSAR", "Dalam Proses"),
            ("11", "Papua", "HEAD OFFICE JAKARTA", "Perlu Tindak Lanjut"),
        ]
        for i, (no, provinsi, kota, status) in enumerate(fallback_meta):
            lat, lng = REGIONAL_COORDS[i]
            regional_locations.append({
                "no": no, "provinsi": provinsi, "kota": kota,
                "status": status, "color": STATUS_COLORS[status],
                "lat": lat, "lng": lng,
                "proyek": "Rehabilitasi Kantor Regional", "dokumen": "-", "keterangan": "-",
                "furniture": "Pengadaan Furniture", "furniture_status": "Dalam Proses",
                "furniture_color": STATUS_COLORS["Dalam Proses"],
            })

    status_counts = {label: sum(1 for l in regional_locations if l['status'] == label)
                      for label, _ in STATUS_LEGEND}

    investasi_kpis = [
        {'title': 'NILAI INVESTASI', 'value': nilai_investasi_short, 'sub': kpi_sub[3],
         'icon': 'payments', 'color': '#F5A623', 'tooltip': kpi_value[3],
         'chart_id': 'investasi-kpi-0', 'chart_option': _echart_line('#F5A623', SPARKS['orange'])},
        {'title': 'JUMLAH ITEM', 'value': str(len(investment_building_all)), 'sub': 'Item investasi tercatat',
         'icon': 'inventory_2', 'color': '#22D3A5', 'tooltip': str(len(investment_building_all)),
         'chart_id': 'investasi-kpi-1', 'chart_option': _echart_line('#22D3A5', SPARKS['green'])},
        {'title': 'ITEM TERBESAR',
         'value': format_rupiah_short(investment_building_all[0]['value']) if investment_building_all else '-',
         'sub': (investment_building_all[0]['name'] if investment_building_all else '-')[:28],
         'icon': 'star', 'color': '#A855F7',
         'tooltip': (investment_building_all[0]['name'] if investment_building_all else '-'),
         'chart_id': 'investasi-kpi-2', 'chart_option': _echart_line('#A855F7', SPARKS['purple'])},
    ]

    charts = {
        'completed_pie': _echart_completed_pie(pekerjaan_selesai, belum_selesai, kpi_value[2]),
        'delivery_bar_mini': _echart_delivery_bar(delivery_perf, full=False),
        'delivery_bar_full': _echart_delivery_bar(delivery_perf, full=True),
        'investment_bar_top10': _echart_investment_bar(investment_building, left=190),
        'investment_bar_all': _echart_investment_bar(investment_building_all, left=220),
    }

    return {
        'generated_at': time.time(),
        'last_update': last_update,
        'kpis': kpis,
        'investasi_kpis': investasi_kpis,
        'total_permohonan': total_permohonan,
        'pekerjaan_selesai': pekerjaan_selesai,
        'belum_selesai': belum_selesai,
        'tower_rows': tower_rows,
        'exec_signal': exec_signal,
        'flow_items': flow_items,
        'delivery_perf': delivery_perf,
        'investment_building': investment_building,
        'investment_building_all': investment_building_all,
        'regional_locations': regional_locations,
        'status_legend': STATUS_LEGEND,
        'status_counts': status_counts,
        'charts': charts,
        'notif_count': len(tower_rows),
    }


_cache = {'data': None, 'ts': 0}
CACHE_TTL_SECONDS = 300


def get_dashboard_data(force_refresh=False):
    now = time.time()
    if force_refresh or _cache['data'] is None or (now - _cache['ts']) > CACHE_TTL_SECONDS:
        _cache['data'] = build_dashboard_data()
        _cache['ts'] = now
    return _cache['data']
