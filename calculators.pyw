# -*- coding: utf-8 -*-
"""
Finansal Hesap Makinesi
=======================
PyQt5 tabanlı sekmeli finansal hesap makinesi.
- Kur Dönüşümü (Frankfurter API + genişletilebilir)
- Yüzde Hesabı (5 farklı mod)
- Vergi İadesi Hesabı (2026 Türkiye vergi dilimleri)
"""

import sys
import json
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QComboBox, QPushButton, QGroupBox,
    QRadioButton, QButtonGroup, QTextEdit, QDoubleSpinBox, QSpinBox,
    QMessageBox, QFrame, QSizePolicy, QSpacerItem, QStatusBar,
    QMenuBar, QMenu, QAction, QActionGroup, QDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QScrollArea, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QLocale, QTimer, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QDoubleValidator, QPainter, QPixmap
try:
    from PyQt5.QtPrintSupport import QPrinter
    HAS_PRINTER = True
except ImportError:
    HAS_PRINTER = False

import requests
try:
    from PyQt5.QtChart import (
        QChart, QChartView, QBarSet, QBarSeries, QLineSeries, 
        QBarCategoryAxis, QValueAxis
    )
    HAS_CHART = True
except ImportError:
    HAS_CHART = False

# ──────────────────────────────────────────────
#  TEMA SİSTEMİ
# ──────────────────────────────────────────────

# Her tema bir renk paleti sözlüğü
THEMES = {
    "Sade": {
        "bg_main": "#f5f5f5", "bg_secondary": "#e8e8e8", "bg_input": "#ffffff",
        "border": "#cccccc", "accent": "#2563eb", "accent_hover": "#3b82f6",
        "accent_pressed": "#1d4ed8", "text": "#1a1a1a", "text_muted": "#555555",
        "text_tab": "#444444", "result": "#16a34a", "textedit": "#1a1a1a",
    },
    "Koyu Mavi": {
        "bg_main": "#1a1a2e", "bg_secondary": "#16213e", "bg_input": "#0f3460",
        "border": "#1a3a6e", "accent": "#f59e0b", "accent_hover": "#fbbf24",
        "accent_pressed": "#d97706", "text": "#ffffff", "text_muted": "#e0e0e0",
        "text_tab": "#a8b2d1", "result": "#10b981", "textedit": "#ccd6f6",
    },
    "Mor Gece": {
        "bg_main": "#1b1030", "bg_secondary": "#2d1b69", "bg_input": "#3b2380",
        "border": "#5533a0", "accent": "#a855f7", "accent_hover": "#c084fc",
        "accent_pressed": "#7c3aed", "text": "#ffffff", "text_muted": "#e0d4f5",
        "text_tab": "#c4b5fd", "result": "#4ade80", "textedit": "#e2d9f3",
    },
    "Yeşil Orman": {
        "bg_main": "#0d1f0d", "bg_secondary": "#1a3a1a", "bg_input": "#254d25",
        "border": "#2d6a2d", "accent": "#22c55e", "accent_hover": "#4ade80",
        "accent_pressed": "#16a34a", "text": "#ffffff", "text_muted": "#d4edda",
        "text_tab": "#a3d9a5", "result": "#fbbf24", "textedit": "#d1e7dd",
    },
    "Okyanus": {
        "bg_main": "#050b14", "bg_secondary": "#0d1b2a", "bg_input": "#1b263b",
        "border": "#1e3a5f", "accent": "#00d4ff", "accent_hover": "#33e0ff",
        "accent_pressed": "#00a3cc", "text": "#ffffff", "text_muted": "#a9d6e5",
        "text_tab": "#89c2d9", "result": "#00f5d4", "textedit": "#e0f1f4",
    },
    "Gün Batımı": {
        "bg_main": "#1f1115", "bg_secondary": "#3b1c27", "bg_input": "#55283a",
        "border": "#7a3a52", "accent": "#f97316", "accent_hover": "#fb923c",
        "accent_pressed": "#ea580c", "text": "#ffffff", "text_muted": "#f5ddd3",
        "text_tab": "#e8a990", "result": "#a3e635", "textedit": "#fde8d8",
    },
}

def generate_style(t: dict) -> str:
    """Tema sözlüğünden CSS üret."""
    return f"""
QMainWindow {{ background-color: {t['bg_main']}; }}
QTabWidget::pane {{
    border: 1px solid {t['bg_secondary']};
    background-color: {t['bg_main']};
    border-radius: 8px;
}}
QTabBar::tab {{
    background-color: {t['bg_secondary']};
    color: {t['text_tab']};
    padding: 8px 24px; margin: 2px 1px;
    border-top-left-radius: 8px; border-top-right-radius: 8px;
    font-size: 13px; font-weight: 600; min-width: 140px; min-height: 24px;
}}
QTabBar::tab:selected {{
    background-color: {t['bg_input']};
    color: {t['accent']};
    border-bottom: 3px solid {t['accent']};
}}
QTabBar::tab:hover {{
    background-color: {t['bg_input']};
    color: {t['accent_hover']};
}}
QGroupBox {{
    background-color: {t['bg_secondary']};
    border: 1px solid {t['bg_input']};
    border-radius: 10px; margin-top: 14px;
    padding: 18px 14px 14px 14px;
    font-size: 13px; font-weight: bold;
    color: {t['accent']};
}}
QGroupBox::title {{
    subcontrol-origin: margin; subcontrol-position: top left;
    padding: 4px 12px;
    background-color: {t['bg_input']};
    border-radius: 6px; color: {t['text']};
}}
QLabel {{ color: {t['text']}; font-size: 12px; }}
QLineEdit, QDoubleSpinBox, QSpinBox {{
    background-color: {t['bg_input']}; color: {t['text']};
    border: 1px solid {t['border']}; border-radius: 6px;
    padding: 8px 12px; font-size: 13px; min-height: 20px;
    selection-background-color: {t['accent']};
}}
QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
    border: 2px solid {t['accent']};
}}
QComboBox {{
    background-color: {t['bg_input']}; color: {t['text']};
    border: 1px solid {t['border']}; border-radius: 6px;
    padding: 8px 30px 8px 12px; font-size: 13px; min-width: 100px; min-height: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {t['bg_secondary']}; color: {t['text']};
    selection-background-color: {t['accent']};
    border: 1px solid {t['bg_input']}; border-radius: 4px;
}}
QPushButton {{
    background-color: {t['accent']}; color: #ffffff;
    border: none; border-radius: 8px;
    padding: 10px 24px; font-size: 13px; font-weight: bold;
}}
QPushButton:hover {{ background-color: {t['accent_hover']}; }}
QPushButton:pressed {{ background-color: {t['accent_pressed']}; }}
QPushButton:disabled {{ background-color: #4a4a6a; color: #888; }}
QRadioButton {{ color: {t['text_tab']}; font-size: 12px; spacing: 8px; }}
QRadioButton::indicator {{
    width: 16px; height: 16px; border-radius: 8px;
    border: 2px solid {t['text_tab']}; background-color: transparent;
}}
QRadioButton::indicator:checked {{
    background-color: {t['accent']}; border-color: {t['accent']};
}}
QTextEdit {{
    background-color: {t['bg_input']}; color: {t['textedit']};
    border: 1px solid {t['border']}; border-radius: 8px;
    padding: 10px; font-size: 12px;
    font-family: 'Consolas', 'Courier New', monospace;
}}
QStatusBar {{
    background-color: {t['bg_secondary']}; color: {t['text_tab']};
    font-size: 11px; border-top: 1px solid {t['bg_input']};
}}
QMenuBar {{
    background-color: {t['bg_secondary']}; color: {t['text']};
    font-size: 12px; border-bottom: 1px solid {t['bg_input']};
}}
QMenuBar::item:selected {{ background-color: {t['bg_input']}; }}
QMenu {{
    background-color: {t['bg_secondary']}; color: {t['text']};
    border: 1px solid {t['bg_input']};
}}
QMenu::item:selected {{ background-color: {t['accent']}; color: #ffffff; }}
QLabel#resultLabel {{
    background-color: {t['bg_input']}; color: {t['result']};
    border: 2px solid {t['border']}; border-radius: 10px;
    padding: 14px; font-size: 18px; font-weight: bold;
    qproperty-alignment: AlignCenter;
}}
QLabel#resultLabelSmall {{
    background-color: {t['bg_input']}; color: {t['result']};
    border: 1px solid {t['border']}; border-radius: 8px;
    padding: 10px; font-size: 14px; font-weight: bold;
    qproperty-alignment: AlignCenter;
}}
QLabel#infoLabel {{ color: {t['text_muted']}; font-size: 11px; font-style: italic; }}
QLabel#headerLabel {{ color: {t['text']}; font-size: 15px; font-weight: bold; }}
QLabel#subHeaderLabel {{ color: {t['accent']}; font-size: 13px; font-weight: bold; }}
QPushButton#toggleBtn {{
    background-color: {t['bg_input']};
    color: {t['text_muted']};
    border: 1px solid {t['border']};
    padding: 4px 12px;
    font-size: 11px;
    font-weight: normal;
}}
QPushButton#toggleBtn:hover {{
    color: {t['accent']};
    background-color: {t['bg_secondary']};
}}
QPushButton#removeBtn {{
    background-color: #991b1b;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: bold;
}}
QPushButton#removeBtn:hover {{
    background-color: #dc2626;
}}
QScrollArea {{
    border: none;
    background-color: transparent;
}}
QScrollArea > QWidget > QWidget {{
    background-color: transparent;
}}
QWidget#contentWidget {{
    background-color: {t['bg_main']};
}}
"""

def get_palette(t: dict) -> QPalette:
    """Tema sözlüğünden QPalette üret."""
    p = QPalette()
    p.setColor(QPalette.Window, QColor(t['bg_main']))
    p.setColor(QPalette.WindowText, QColor(t['text_tab']))
    p.setColor(QPalette.Base, QColor(t['bg_input']))
    p.setColor(QPalette.AlternateBase, QColor(t['bg_secondary']))
    p.setColor(QPalette.ToolTipBase, QColor(t['bg_secondary']))
    p.setColor(QPalette.ToolTipText, QColor(t['text']))
    p.setColor(QPalette.Text, QColor(t['text']))
    p.setColor(QPalette.Button, QColor(t['bg_secondary']))
    p.setColor(QPalette.ButtonText, QColor(t['text']))
    p.setColor(QPalette.Highlight, QColor(t['accent']))
    p.setColor(QPalette.HighlightedText, QColor('#ffffff'))
    return p

# ──────────────────────────────────────────────
#  KUR SAĞLAYICILARI (Genişletilebilir)
# ──────────────────────────────────────────────

# Uygulama dizini (EXE durumunda EXE'nin bulunduğu klasör, çalışma dizini için)
if getattr(sys, 'frozen', False):
    APP_DIR = Path(sys.executable).parent
else:
    APP_DIR = Path(__file__).parent

SETTINGS_FILE = APP_DIR / "settings.json"
CACHE_FILE = APP_DIR / "rates_cache.json"

def load_settings():
    """Ayarlar dosyasını yükle veya varsayılanla oluştur."""
    default = {
        "active_provider": "exchangerate",
        "providers": {
            "exchangerate": {
                "name": "ExchangeRate API (Ücretsiz)",
                "base_url": "https://open.er-api.com/v6",
                "api_key": ""
            }
        },
        "cache_ttl_seconds": 600,
        "tax_settings": {
            "asgari_ucret_yillik": 396360.0,
            "ucret_dilimleri": [
                [190000.0, 0.15],
                [400000.0, 0.20],
                [1500000.0, 0.27],
                [5300000.0, 0.35],
                [9999999999.0, 0.40]
            ],
            "ucret_disi_dilimleri": [
                [190000.0, 0.15],
                [400000.0, 0.20],
                [1000000.0, 0.27],
                [5300000.0, 0.35],
                [9999999999.0, 0.40]
            ]
        }
    }
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Eksik anahtarları tamamla
            for k, v in default.items():
                data.setdefault(k, v)
            return data
        except Exception:
            pass
    # İlk çalıştırmada varsayılanı kaydet
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(default, f, indent=2, ensure_ascii=False)
    return default


class RateProvider(ABC):
    """Kur sağlayıcı soyut temel sınıf.
    Yeni bir kaynak eklemek için bu sınıfı alt-sınıflayın."""

    @abstractmethod
    def fetch_rates(self, base_currency: str) -> dict:
        """base_currency'ye göre tüm kurları dict olarak döndür.
        Örn: {'USD': 1.0, 'TRY': 36.2, ...}"""
        ...

    @abstractmethod
    def get_currencies(self) -> dict:
        """Desteklenen para birimleri {kod: isim} döndür."""
        ...


# Yaygın para birimleri (statik liste – API bağımlılığı yok)
CURRENCY_NAMES = {
    "TRY": "Türk Lirası", "USD": "ABD Doları", "EUR": "Euro",
    "GBP": "İngiliz Sterlini", "JPY": "Japon Yeni", "CHF": "İsviçre Frangı",
    "CAD": "Kanada Doları", "AUD": "Avustralya Doları", "CNY": "Çin Yuanı",
    "RUB": "Rus Rublesi", "KRW": "Güney Kore Wonu", "INR": "Hindistan Rupisi",
    "BRL": "Brezilya Reali", "MXN": "Meksika Pesosu", "ZAR": "Güney Afrika Randı",
    "SEK": "İsveç Kronu", "NOK": "Norveç Kronu", "DKK": "Danimarka Kronu",
    "PLN": "Polonya Zlotisi", "CZK": "Çek Korunası", "HUF": "Macar Forinti",
    "RON": "Romen Leyi", "BGN": "Bulgar Levası", "HRK": "Hırvat Kunası",
    "SAR": "Suudi Riyali", "AED": "BAE Dirhemi", "QAR": "Katar Riyali",
    "KWD": "Kuveyt Dinarı", "EGP": "Mısır Lirası", "AZN": "Azerbaycan Manatı",
    "GEL": "Gürcistan Larisi", "SGD": "Singapur Doları", "HKD": "Hong Kong Doları",
    "TWD": "Tayvan Doları", "THB": "Tayland Bahtı", "MYR": "Malezya Ringgiti",
    "IDR": "Endonezya Rupisi", "PHP": "Filipin Pesosu", "NZD": "Yeni Zelanda Doları",
    "ILS": "İsrail Şekeli", "PKR": "Pakistan Rupisi", "NGN": "Nijerya Nairası",
    "ARS": "Arjantin Pesosu", "CLP": "Şili Pesosu", "COP": "Kolombiya Pesosu",
    "PEN": "Peru Solü", "UAH": "Ukrayna Grivnası",
}


class ExchangeRateProvider(RateProvider):
    """ExchangeRate API – ücretsiz, API key gereksiz, 1500+ para birimi."""

    def __init__(self, base_url="https://open.er-api.com/v6"):
        self.base_url = base_url.rstrip("/")

    def fetch_rates(self, base_currency: str) -> dict:
        url = f"{self.base_url}/latest/{base_currency}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("result") != "success":
            raise Exception(data.get("error-type", "Bilinmeyen hata"))
        rates = data.get("rates", {})
        return rates

    def get_currencies(self) -> dict:
        return CURRENCY_NAMES


# Sağlayıcı fabrikası
def create_provider(settings: dict) -> RateProvider:
    name = settings.get("active_provider", "exchangerate")
    cfg = settings.get("providers", {}).get(name, {})
    if name == "exchangerate":
        return ExchangeRateProvider(cfg.get("base_url", "https://open.er-api.com/v6"))
    # Gelecekte başka sağlayıcılar buraya eklenir
    return ExchangeRateProvider()


# ──────────────────────────────────────────────
#  ARKA PLAN İŞ PARÇACIKLARI
# ──────────────────────────────────────────────

class FetchRatesThread(QThread):
    """Kur verilerini arka planda çeker."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, provider: RateProvider, base_currency: str):
        super().__init__()
        self.provider = provider
        self.base = base_currency

    def run(self):
        try:
            rates = self.provider.fetch_rates(self.base)
            self.finished.emit(rates)
        except Exception as e:
            self.error.emit(str(e))


class FetchCurrenciesThread(QThread):
    """Para birimi listesini arka planda çeker."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, provider: RateProvider):
        super().__init__()
        self.provider = provider

    def run(self):
        try:
            currencies = self.provider.get_currencies()
            self.finished.emit(currencies)
        except Exception as e:
            self.error.emit(str(e))


# ──────────────────────────────────────────────
#  SEKME 1: KUR DÖNÜŞÜMÜ
# ──────────────────────────────────────────────

class CurrencyTab(QWidget):
    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings
        self.provider = create_provider(settings)
        self.rates_cache = {}
        self.cache_time = 0
        self.cache_ttl = settings.get("cache_ttl_seconds", 600)
        self.currencies = {}
        self._thread = None
        self._curr_thread = None
        self._init_ui()
        self._load_currencies()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        layout = QVBoxLayout(content_widget)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        layout.setSpacing(14)

        # Başlık
        header = QLabel("💱 Döviz Kuru Dönüştürücü")
        header.setObjectName("headerLabel")
        layout.addWidget(header)

        info = QLabel("Kurlar ExchangeRate API üzerinden anlık olarak alınır. "
                       "Ayarlar settings.json dosyasından yapılandırılabilir.")
        info.setObjectName("infoLabel")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Dönüşüm grubu
        group = QGroupBox("Dönüşüm")
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(QLabel("Miktar:"), 0, 0)
        self.amount_input = QLineEdit("1")
        self.amount_input.setValidator(QDoubleValidator(0, 999999999999, 6))
        self.amount_input.setPlaceholderText("Miktar girin...")
        grid.addWidget(self.amount_input, 0, 1)

        grid.addWidget(QLabel("Kaynak:"), 1, 0)
        self.from_combo = QComboBox()
        grid.addWidget(self.from_combo, 1, 1)

        grid.addWidget(QLabel("Hedef:"), 2, 0)
        self.to_combo = QComboBox()
        grid.addWidget(self.to_combo, 2, 1)

        # Takas butonu
        swap_btn = QPushButton("⇅ Değiştir")
        swap_btn.setFixedWidth(120)
        swap_btn.clicked.connect(self._swap_currencies)
        grid.addWidget(swap_btn, 1, 2, 2, 1)

        self.convert_btn = QPushButton("Dönüştür")
        self.convert_btn.clicked.connect(self._convert)
        grid.addWidget(self.convert_btn, 3, 0, 1, 3)

        group.setLayout(grid)
        layout.addWidget(group)

        # Sonuç
        self.result_label = QLabel("")
        self.result_label.setObjectName("resultLabel")
        self.result_label.setMinimumHeight(60)
        self.result_label.hide()
        layout.addWidget(self.result_label)

        # Son güncelleme
        self.update_label = QLabel("")
        self.update_label.setObjectName("infoLabel")
        self.update_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.update_label)

        layout.addStretch()

    def _load_currencies(self):
        """Para birimi listesini API'den çek."""
        self._curr_thread = FetchCurrenciesThread(self.provider)
        self._curr_thread.finished.connect(self._on_currencies_loaded)
        self._curr_thread.error.connect(self._on_currencies_error)
        self._curr_thread.start()

    def _on_currencies_loaded(self, currencies: dict):
        self.currencies = currencies
        self.from_combo.clear()
        self.to_combo.clear()

        # Öncelikli paralar üstte
        priority = ["TRY", "USD", "EUR", "GBP"]
        sorted_codes = sorted(currencies.keys())
        ordered = [c for c in priority if c in sorted_codes]
        ordered += [c for c in sorted_codes if c not in priority]

        for code in ordered:
            label = f"{code} – {currencies[code]}"
            self.from_combo.addItem(label, code)
            self.to_combo.addItem(label, code)

        # Varsayılan: USD → TRY
        idx_usd = ordered.index("USD") if "USD" in ordered else 0
        idx_try = ordered.index("TRY") if "TRY" in ordered else 1
        self.from_combo.setCurrentIndex(idx_usd)
        self.to_combo.setCurrentIndex(idx_try)

    def _on_currencies_error(self, err: str):
        # Çevrimdışı fallback
        fallback = {"USD": "ABD Doları", "EUR": "Euro", "GBP": "İngiliz Sterlini",
                     "TRY": "Türk Lirası", "JPY": "Japon Yeni", "CHF": "İsviçre Frangı",
                     "CAD": "Kanada Doları", "AUD": "Avustralya Doları", "CNY": "Çin Yuanı"}
        self._on_currencies_loaded(fallback)
        self.update_label.setText(f"⚠ Para listesi yüklenemedi: {err}")

    def _swap_currencies(self):
        i, j = self.from_combo.currentIndex(), self.to_combo.currentIndex()
        self.from_combo.setCurrentIndex(j)
        self.to_combo.setCurrentIndex(i)

    def _convert(self):
        try:
            amount = float(self.amount_input.text().replace(",", "."))
        except ValueError:
            self.result_label.setText("⚠ Geçerli bir miktar girin")
            return

        base = self.from_combo.currentData()
        target = self.to_combo.currentData()
        if not base or not target:
            return

        if base == target:
            self.result_label.setText(f"{amount:,.6g} {base} = {amount:,.6g} {target}")
            return

        now = time.time()
        # Önbellek kontrolü
        if base in self.rates_cache and (now - self.cache_time) < self.cache_ttl:
            self._do_convert(amount, base, target, self.rates_cache[base])
            return

        self.convert_btn.setEnabled(False)
        self.convert_btn.setText("Yükleniyor...")
        self._amount_pending = amount
        self._base_pending = base
        self._target_pending = target

        self._thread = FetchRatesThread(self.provider, base)
        self._thread.finished.connect(self._on_rates_fetched)
        self._thread.error.connect(self._on_rates_error)
        self._thread.start()

    def _on_rates_fetched(self, rates: dict):
        self.rates_cache[self._base_pending] = rates
        self.cache_time = time.time()
        self._do_convert(self._amount_pending, self._base_pending, self._target_pending, rates)
        self.convert_btn.setEnabled(True)
        self.convert_btn.setText("Dönüştür")
        self.update_label.setText(f"✓ Kurlar güncellendi: {time.strftime('%H:%M:%S')}")
        
        # Diske kaydet
        try:
            cache_data = {}
            if CACHE_FILE.exists():
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
            cache_data[self._base_pending] = {
                "rates": rates,
                "timestamp": self.cache_time
            }
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False)
        except Exception:
            pass

    def _on_rates_error(self, err: str):
        # İnternet yoksa diske bak
        try:
            if CACHE_FILE.exists():
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                
                if self._base_pending in cache_data:
                    stored = cache_data[self._base_pending]
                    rates = stored["rates"]
                    ts = stored["timestamp"]
                    dt_str = time.strftime('%d.%m.%Y %H:%M', time.localtime(ts))
                    
                    self.rates_cache[self._base_pending] = rates
                    self._do_convert(self._amount_pending, self._base_pending, self._target_pending, rates)
                    self.convert_btn.setEnabled(True)
                    self.convert_btn.setText("Dönüştür")
                    self.update_label.setText(f"⚠ Çevrimdışı (Son güncel: {dt_str})")
                    return
        except Exception:
            pass
            
        self.result_label.setText(f"⚠ Hata (İnternet Yok): {err}")
        self.convert_btn.setEnabled(True)
        self.convert_btn.setText("Dönüştür")

    def _do_convert(self, amount, base, target, rates):
        if target not in rates:
            self.result_label.setText(f"⚠ {target} kuru bulunamadı")
            return
        rate = rates[target]
        result = amount * rate
        self.result_label.setVisible(True)
        self.result_label.setText(
            f"{amount:,.2f} {base}  =  {result:,.2f} {target}\n"
            f"1 {base} = {rate:,.6f} {target}"
        )


# ──────────────────────────────────────────────
#  SEKME 2: YÜZDE HESABI
# ──────────────────────────────────────────────

class PercentTab(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        layout = QVBoxLayout(content_widget)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        layout.setSpacing(12)

        header = QLabel("📊 Yüzde Hesaplayıcı")
        header.setObjectName("headerLabel")
        layout.addWidget(header)

        # Mod seçimi
        mode_group = QGroupBox("Hesaplama Modu")
        mode_layout = QVBoxLayout()
        self.mode_bg = QButtonGroup(self)

        modes = [
            ("Bir sayının %X'i kaçtır?", "X sayısının %Y'si = ?"),
            ("X, Y'nin yüzde kaçıdır?", "X değeri, Y değerinin yüzde kaçı?"),
            ("Yüzde değişim (artış/azalış)", "Eski → Yeni, % kaç değişim?"),
            ("İki değer arası yüzdelik fark", "A ile B arasındaki % fark"),
            ("KDV Hesaplama", "KDV dahil ↔ hariç dönüşüm"),
        ]

        for i, (title, desc) in enumerate(modes):
            rb = QRadioButton(f"{title}   ({desc})")
            rb.setStyleSheet("font-size: 12px;")
            self.mode_bg.addButton(rb, i)
            mode_layout.addWidget(rb)

        self.mode_bg.button(0).setChecked(True)
        self.mode_bg.idClicked.connect(self._on_mode_changed)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Girişler
        input_group = QGroupBox("Değerler")
        input_grid = QGridLayout()
        input_grid.setSpacing(10)

        self.lbl_a = QLabel("Sayı (X):")
        self.input_a = QLineEdit()
        self.input_a.setPlaceholderText("Değer girin...")
        self.input_a.setValidator(QDoubleValidator())
        input_grid.addWidget(self.lbl_a, 0, 0)
        input_grid.addWidget(self.input_a, 0, 1)

        self.lbl_b = QLabel("Yüzde (%):")
        self.input_b = QLineEdit()
        self.input_b.setPlaceholderText("Değer girin...")
        self.input_b.setValidator(QDoubleValidator())
        input_grid.addWidget(self.lbl_b, 1, 0)
        input_grid.addWidget(self.input_b, 1, 1)

        # KDV oranı (sadece mod 4 için)
        self.lbl_kdv = QLabel("KDV Oranı (%):")
        self.kdv_combo = QComboBox()
        self.kdv_combo.addItems(["1", "10", "20"])
        self.kdv_combo.setCurrentIndex(2)
        self.lbl_kdv.hide()
        self.kdv_combo.hide()
        input_grid.addWidget(self.lbl_kdv, 2, 0)
        input_grid.addWidget(self.kdv_combo, 2, 1)

        # KDV yönü
        self.kdv_direction = QComboBox()
        self.kdv_direction.addItems(["KDV Hariç → KDV Dahil", "KDV Dahil → KDV Hariç"])
        self.kdv_direction.hide()
        input_grid.addWidget(self.kdv_direction, 3, 0, 1, 2)

        input_group.setLayout(input_grid)
        layout.addWidget(input_group)

        # Hesapla butonu
        calc_btn = QPushButton("Hesapla")
        calc_btn.clicked.connect(self._calculate)
        layout.addWidget(calc_btn)

        # Sonuç
        self.result_label = QLabel("")
        self.result_label.setObjectName("resultLabel")
        self.result_label.setMinimumHeight(60)
        self.result_label.setWordWrap(True)
        self.result_label.hide()
        layout.addWidget(self.result_label)

        # Detay
        self.detail_label = QLabel("")
        self.detail_label.setObjectName("infoLabel")
        self.detail_label.setWordWrap(True)
        self.detail_label.hide()
        layout.addWidget(self.detail_label)

        layout.addStretch()
        self._on_mode_changed(0)

    def _on_mode_changed(self, mode_id):
        labels_a = ["Sayı (X):", "Parça (X):", "Eski Değer:", "Değer A:", "Tutar:"]
        labels_b = ["Yüzde (%):", "Bütün (Y):", "Yeni Değer:", "Değer B:", "—"]
        self.lbl_a.setText(labels_a[mode_id])
        self.lbl_b.setText(labels_b[mode_id])

        is_kdv = mode_id == 4
        self.lbl_b.setVisible(not is_kdv)
        self.input_b.setVisible(not is_kdv)
        self.lbl_kdv.setVisible(is_kdv)
        self.kdv_combo.setVisible(is_kdv)
        self.kdv_direction.setVisible(is_kdv)

        self.input_a.clear()
        self.input_b.clear()
        self.result_label.hide()
        self.detail_label.hide()
        self.result_label.setText("")
        self.detail_label.setText("")

    def _parse(self, line_edit: QLineEdit) -> float:
        text = line_edit.text().replace(",", ".").replace(" ", "")
        return float(text)

    def _calculate(self):
        mode = self.mode_bg.checkedId()
        try:
            a = self._parse(self.input_a)
        except ValueError:
            self.result_label.setText("⚠ Geçerli bir sayı girin (ilk kutu)")
            return

        if mode != 4:
            try:
                b = self._parse(self.input_b)
            except ValueError:
                self.result_label.setText("⚠ Geçerli bir sayı girin (ikinci kutu)")
                return

        if mode == 0:
            # X'in %Y'si
            result = a * b / 100
            self.result_label.setVisible(True)
            self.detail_label.setVisible(True)
            self.result_label.setText(f"{a:,.4g} sayısının %{b:g}'{'s' if b != 1 else ''}i = {result:,.4g}")
            self.detail_label.setText(f"Formül: {a} × {b} / 100 = {result:,.6g}")

        elif mode == 1:
            # X, Y'nin % kaçı
            if b == 0:
                self.result_label.setText("⚠ Bütün (Y) değeri sıfır olamaz")
                return
            pct = (a / b) * 100
            self.result_label.setVisible(True)
            self.detail_label.setVisible(True)
            self.result_label.setText(f"{a:,.4g},  {b:,.4g} değerinin %{pct:,.4g}'{'s' if pct != 1 else ''}idir")
            self.detail_label.setText(f"Formül: ({a} / {b}) × 100 = %{pct:,.6g}")

        elif mode == 2:
            # Yüzde değişim
            if a == 0:
                self.result_label.setText("⚠ Eski değer sıfır olamaz")
                return
            change = ((b - a) / abs(a)) * 100
            direction = "artış 📈" if change >= 0 else "azalış 📉"
            self.result_label.setVisible(True)
            self.detail_label.setVisible(True)
            self.result_label.setText(f"%{abs(change):,.4g} {direction}")
            self.detail_label.setText(
                f"Formül: (({b} - {a}) / |{a}|) × 100 = %{change:,.6g}\n"
                f"Fark: {b - a:,.4g}"
            )

        elif mode == 3:
            # Yüzdelik fark
            avg = (abs(a) + abs(b)) / 2
            if avg == 0:
                self.result_label.setText("⚠ Her iki değer de sıfır olamaz")
                return
            diff = (abs(a - b) / avg) * 100
            self.result_label.setVisible(True)
            self.detail_label.setVisible(True)
            self.result_label.setText(f"Yüzdelik fark: %{diff:,.4g}")
            self.detail_label.setText(
                f"Formül: |{a} - {b}| / ((|{a}| + |{b}|) / 2) × 100 = %{diff:,.6g}\n"
                f"Mutlak fark: {abs(a - b):,.4g}  |  Ortalama: {avg:,.4g}"
            )

        elif mode == 4:
            # KDV
            kdv_rate = float(self.kdv_combo.currentText())
            direction_idx = self.kdv_direction.currentIndex()
            if direction_idx == 0:
                # Hariç → Dahil
                kdv_amount = a * kdv_rate / 100
                total = a + kdv_amount
                self.result_label.setVisible(True)
                self.detail_label.setVisible(True)
                self.result_label.setText(f"KDV Dahil: {total:,.2f}")
                self.detail_label.setText(
                    f"KDV Hariç Tutar: {a:,.2f}\n"
                    f"KDV Tutarı (%{kdv_rate:g}): {kdv_amount:,.2f}\n"
                    f"KDV Dahil Toplam: {total:,.2f}"
                )
            else:
                # Dahil → Hariç
                base_amount = a / (1 + kdv_rate / 100)
                kdv_amount = a - base_amount
                self.result_label.setVisible(True)
                self.detail_label.setVisible(True)
                self.result_label.setText(f"KDV Hariç: {base_amount:,.2f}")
                self.detail_label.setText(
                    f"KDV Dahil Tutar: {a:,.2f}\n"
                    f"KDV Tutarı (%{kdv_rate:g}): {kdv_amount:,.2f}\n"
                    f"KDV Hariç Tutar: {base_amount:,.2f}"
                )


# ──────────────────────────────────────────────
#  SEKME 3: VERGİ İADESİ HESABI
# ──────────────────────────────────────────────

CURRENT_YEAR = datetime.now().year

# 2026 Yıllık brüt asgari ücret
YILLIK_BRUT_ASG_UCRET_2026 = 33_030.00 * 12  # 396.360 TL

# 2026 Gelir vergisi dilimleri – ÜCRET gelirleri
UCRET_VERGI_DILIMLERI_2026 = [
    (190_000,    0.15),
    (400_000,    0.20),
    (1_500_000,  0.27),
    (5_300_000,  0.35),
    (float('inf'), 0.40),
]

# 2026 Gelir vergisi dilimleri – ÜCRET DIŞI gelirler
UCRET_DISI_VERGI_DILIMLERI_2026 = [
    (190_000,    0.15),
    (400_000,    0.20),
    (1_000_000,  0.27),
    (5_300_000,  0.35),
    (float('inf'), 0.40),
]


# ──────────────────────────────────────────────
#  SİGORTA POLİÇE SATIRI
# ──────────────────────────────────────────────

class InsuranceItemWidget(QWidget):
    removed = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 5, 0, 5)

        self.ay_combo = QComboBox()
        self.ay_combo.addItems(["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"])
        self.ay_combo.setFixedWidth(100)
        
        self.tip_combo = QComboBox()
        self.tip_combo.addItems(["Birikimli Hayat (%50)", "Sağlık/Vefat (%100)"])
        self.tip_combo.setFixedWidth(190)
        self.tip_combo.setCurrentIndex(1) # Varsayılan: Vefat

        self.prim_input = QLineEdit("100") # Varsayılan: 100 
        self.prim_input.setPlaceholderText("Prim")
        self.prim_input.setValidator(QDoubleValidator(0, 999999999, 2))
        
        self.remove_btn = QPushButton("✕")
        self.remove_btn.setFixedSize(34, 34)
        self.remove_btn.setObjectName("removeBtn")
        self.remove_btn.setToolTip("Poliçeyi Sil")
        self.remove_btn.clicked.connect(lambda: self.removed.emit(self))

        self.layout.addWidget(QLabel("Başlangıç:"))
        self.layout.addWidget(self.ay_combo)
        self.layout.addWidget(QLabel("Tür:"))
        self.layout.addWidget(self.tip_combo)
        self.layout.addWidget(QLabel("Prim:"))
        self.layout.addWidget(self.prim_input)
        self.layout.addWidget(self.remove_btn)

    def get_data(self):
        try:
            val = float(self.prim_input.text().replace(",", ".").replace(" ", ""))
        except:
            val = 0.0
        return {
            "ay_idx": self.ay_combo.currentIndex(),
            "is_hayat": self.tip_combo.currentIndex() == 0,
            "prim": val
        }


def hesapla_vergi(yillik_brut: float, dilimler: list) -> tuple:
    """Artan oranlı gelir vergisi hesapla.
    Döndürür: (toplam_vergi, dilim_detaylari_listesi)
    """
    kalan = yillik_brut
    toplam_vergi = 0
    alt_sinir = 0
    detaylar = []

    for ust_sinir, oran in dilimler:
        if kalan <= 0:
            break
        dilim_genislik = ust_sinir - alt_sinir
        vergilenecek = min(kalan, dilim_genislik)
        dilim_vergi = vergilenecek * oran
        toplam_vergi += dilim_vergi
        detaylar.append({
            "alt": alt_sinir,
            "ust": min(ust_sinir, yillik_brut),
            "oran": oran,
            "matrah": vergilenecek,
            "vergi": dilim_vergi
        })
        kalan -= vergilenecek
        alt_sinir = ust_sinir

    return toplam_vergi, detaylar


def marjinal_vergi_orani(yillik_brut: float, dilimler: list) -> float:
    """Kişinin bulunduğu en üst vergi dilim oranını döndür."""
    alt = 0
    for ust, oran in dilimler:
        if yillik_brut <= ust:
            return oran
        alt = ust
    return dilimler[-1][1]


class TaxTab(QWidget):
    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        layout = QVBoxLayout(content_widget)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        layout.setSpacing(12)

        header = QLabel(f"🏛️ Gelir Vergisi & Sigorta İadesi Hesaplama ({CURRENT_YEAR})")
        header.setObjectName("headerLabel")
        layout.addWidget(header)

        info = QLabel(f"{CURRENT_YEAR} yılı gelir vergisi dilimleri ve hayat sigortası prim indirimi hesabı. "
                       "Vergi dilimleri Hazine ve Maliye Bakanlığı tebliğine göre güncellenmiştir.")
        info.setObjectName("infoLabel")
        info.setWordWrap(True)
        layout.addWidget(info)

        # — Gelir Bilgileri —
        income_group = QGroupBox("Gelir Bilgileri")
        ig = QGridLayout()
        ig.setContentsMargins(10, 20, 10, 10)
        ig.setHorizontalSpacing(15)
        ig.setVerticalSpacing(20)

        ig.addWidget(QLabel("Gelir Türü:"), 0, 0)
        self.income_type = QComboBox()
        self.income_type.addItems(["Ücret Geliri (maaşlı çalışan)", "Ücret Dışı Gelir (serbest meslek vb.)"])
        ig.addWidget(self.income_type, 0, 1)

        ig.addWidget(QLabel("Brüt Gelir (₺):"), 1, 0)
        self.brut_input = QLineEdit()
        self.brut_input.setPlaceholderText("Örn: 50000")
        self.brut_input.setValidator(QDoubleValidator(0, 999999999999, 2))
        ig.addWidget(self.brut_input, 1, 1)

        ig.setRowStretch(2, 1)

        income_group.setLayout(ig)
        layout.addWidget(income_group)

        # — Sigorta Primleri —
        self.ins_group = QGroupBox("Sigorta Prim Bilgileri")
        
        # Toggle Butonu
        toggle_layout = QHBoxLayout()
        toggle_layout.addStretch()
        self.toggle_btn = QPushButton("➖ Sigorta Gizle/Daralt")
        self.toggle_btn.setObjectName("toggleBtn")
        self.toggle_btn.setFixedWidth(150)
        self.toggle_btn.clicked.connect(self._toggle_insurance)
        toggle_layout.addWidget(self.toggle_btn)
        layout.addLayout(toggle_layout)

        self.ins_group.setMinimumHeight(120)
        self.ins_container = QWidget()
        self.ins_v_layout = QVBoxLayout(self.ins_container)
        
        # Para birimi ve Ekle butonu satırı
        top_h = QHBoxLayout()
        top_h.addWidget(QLabel("Para Birimi:"))
        self.kur_combo = QComboBox()
        self.kur_combo.addItems(["TRY (₺)", "USD ($)"])
        self.kur_combo.setCurrentIndex(1) # Varsayılan: USD
        self.kur_combo.currentIndexChanged.connect(self._on_curr_changed)
        top_h.addWidget(self.kur_combo)
        
        self.usd_lbl = QLabel("Kur:")
        self.usd_input = QLineEdit("43.85")
        self.usd_input.setValidator(QDoubleValidator(0, 999, 4))
        # USD varsayılan olduğu için başlangıçta göster
        self.usd_lbl.show()
        self.usd_input.show()
        top_h.addWidget(self.usd_lbl)
        top_h.addWidget(self.usd_input)
        
        top_h.addStretch()
        self.add_poli_btn = QPushButton("➕ Poliçe Ekle")
        self.add_poli_btn.setFixedWidth(135)
        self.add_poli_btn.clicked.connect(self._add_policy)
        top_h.addWidget(self.add_poli_btn)
        self.ins_v_layout.addLayout(top_h)

        # Poliçelerin listeleneceği alan
        self.poli_list_layout = QVBoxLayout()
        self.ins_v_layout.addLayout(self.poli_list_layout)
        self.poli_widgets = []
        
        # İlk boş poliçeyi ekle
        self._add_policy()

        note = QLabel("ℹ Seçilen aydan itibaren ödenen primler üzerinden net iadeler hesaplanır.\nÜst sınır Yıllık Brüt Asgari Ücrettir.")
        note.setObjectName("infoLabel")
        note.setWordWrap(True)
        self.ins_v_layout.addWidget(note)


        inner_v = QVBoxLayout(self.ins_group)
        inner_v.setContentsMargins(10, 20, 10, 10)
        inner_v.addWidget(self.ins_container)
        layout.addWidget(self.ins_group)

        # Hesapla ve Detay Butonları
        btn_layout = QHBoxLayout()
        calc_btn = QPushButton("Hesapla")
        calc_btn.clicked.connect(self._calculate)
        btn_layout.addWidget(calc_btn)
        
        self.details_btn = QPushButton("📋 Sonuç Detayları")
        self.details_btn.setObjectName("toggleBtn") # Benzer stil kullansın
        self.details_btn.clicked.connect(self._show_details_popup)
        self.details_btn.setVisible(False)
        self.details_btn.setFixedWidth(160)
        self.details_btn.setToolTip("Tüm hesaplama dökümünü yeni pencerede gör ve kopyala")
        btn_layout.addWidget(self.details_btn)
        
        layout.addLayout(btn_layout)

        # Sonuç alanı
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumHeight(200)
        self.result_text.hide()
        layout.addWidget(self.result_text)
        layout.addStretch(1)



    def _add_policy(self):
        w = InsuranceItemWidget()
        w.removed.connect(self._remove_policy)
        self.poli_list_layout.addWidget(w)
        self.poli_widgets.append(w)

    def _remove_policy(self, widget):
        if len(self.poli_widgets) > 1:
            widget.setParent(None)
            self.poli_widgets.remove(widget)
        else:
            QMessageBox.warning(self, "Uyarı", "En az bir poliçe satırı bulunmalıdır.")

    def _toggle_insurance(self):
        is_visible = self.ins_group.isVisible()
        self.ins_group.setVisible(not is_visible)
        self.toggle_btn.setText("➕ Sigorta Ekle/Genişlet" if is_visible else "➖ Sigorta Gizle/Daralt")

    def _on_curr_changed(self, idx):
        is_usd = (idx == 1)
        self.usd_lbl.setVisible(is_usd)
        self.usd_input.setVisible(is_usd)

    def _parse(self, le: QLineEdit) -> float:
        t = le.text().replace(",", ".").replace(" ", "").replace("₺", "").replace("$", "")
        return float(t) if t else 0.0

    def _calculate(self):
        ts = self.settings.get("tax_settings", {})
        asgari_ucret = ts.get("asgari_ucret_yillik", 396360.0)
        ucret_dilimleri = ts.get("ucret_dilimleri", [[190_000, 0.15], [400_000, 0.20], [1_500_000, 0.27], [5_300_000, 0.35], [9999999999.0, 0.40]])
        ucret_disi_dilimleri = ts.get("ucret_disi_dilimleri", [[190_000, 0.15], [400_000, 0.20], [1_000_000, 0.27], [5_300_000, 0.35], [9999999999.0, 0.40]])

        try:
            brut_aylik = self._parse(self.brut_input)
        except ValueError:
            brut_aylik = 0.0

        if brut_aylik <= 0:
            brut_aylik = asgari_ucret / 12
            self.brut_input.setText(f"{brut_aylik:.2f}")

        is_usd = (self.kur_combo.currentIndex() == 1)
        usd_kuru = self._parse(self.usd_input) if is_usd else 1.0

        # Dinamik poliçeleri topla
        poli_aylik_matrahlar = [0.0] * 12 # 12 aya dağılacak indirimler
        toplam_indirilecek_yillik = 0.0

        for w in self.poli_widgets:
            data = w.get_data()
            ay_idx = data["ay_idx"]
            prim_try = data["prim"] * usd_kuru
            oran = 0.5 if data["is_hayat"] else 1.0
            
            aylık_indirilecek = prim_try * oran
            # Poliçe başlangıç ayından itibaren yıl sonuna kadar ekle
            for i in range(ay_idx, 12):
                poli_aylik_matrahlar[i] += aylık_indirilecek
            
            toplam_indirilecek_yillik += aylık_indirilecek * (12 - ay_idx)

        # Vergi dilimleri yıllıktır
        brut = brut_aylik * 12
        
        is_ucret = self.income_type.currentIndex() == 0
        dilimler = ucret_dilimleri if is_ucret else ucret_disi_dilimleri
        gelir_turu = "Ücret Geliri" if is_ucret else "Ücret Dışı Gelir"
        
        # MATRAH HESABI: Gelir Vergisi matrahı üzerinden hesaplanır.
        yillik_matrah = brut
        if is_ucret:
            tavan_aylik = asgari_ucret / 12 * 7.5
            prime_esas_aylik = min(brut_aylik, tavan_aylik)
            sgk_issizlik = prime_esas_aylik * 0.15 
            yillik_matrah = (brut_aylik - sgk_issizlik) * 12

        # 1) Vergi hesabı (indirim öncesi) - Matrah Üzerinden!
        vergi_oncesi, oncesi_detay = hesapla_vergi(yillik_matrah, dilimler)

        # 2) Sigorta indirimi hesabı (Yıllık üst sınır kontrolü)
        ust_sinir_gelir = brut * 0.15
        ust_sinir_asgari = asgari_ucret
        ust_sinir = min(ust_sinir_gelir, ust_sinir_asgari)

        indirim_uygulanacak_yillik = min(toplam_indirilecek_yillik, ust_sinir)

        # 3) İndirim sonrası matrah ve vergi
        matrah_sonrasi = max(yillik_matrah - indirim_uygulanacak_yillik, 0)
        vergi_sonrasi, sonrasi_detay = hesapla_vergi(matrah_sonrasi, dilimler)

        # 4) Vergi iadesi
        vergi_iadesi = vergi_oncesi - vergi_sonrasi
        
        # Aylara göre yansıyan saf iadeleri hesaplamak için aylık limit kontrolü
        # (Yıllık indirim limitini aylara bölerek aşmamayı sağlarız)
        kalan_limit_yillik = indirim_uygulanacak_yillik

        marjinal = marjinal_vergi_orani(yillik_matrah, dilimler)

        # — Rapor —
        lines = []
        lines.append("=" * 65)
        lines.append(f"  VERGİ & SİGORTA İADESİ HESAPLAMA RAPORU ({CURRENT_YEAR})")
        lines.append("=" * 65)
        lines.append("")
        lines.append(f"  Gelir Türü       : {gelir_turu}")
        lines.append(f"  Aylık Brüt Gelir : {brut_aylik:>15,.2f} ₺")
        if is_ucret:
            lines.append(f"  Ayl. Vergi Matrahı: {(yillik_matrah/12):>14,.2f} ₺")
        lines.append(f"  Marjinal Dilim   : %{marjinal * 100:.0f}")
        lines.append("")

        lines.append("─── YILLIK VERGİ DİLİMLERİ (İndirim Öncesi) ───")
        for d in oncesi_detay:
            ust_str = f"{d['ust']:,.0f}" if d['ust'] < 1e15 else "∞"
            lines.append(f"  {d['alt']:>10,.0f} – {ust_str:>10} ₺ %{d['oran'] * 100:>2.0f} → Vergi: {d['vergi']:>10,.2f} ₺")
        lines.append(f"  {'':>30} TOPLAM: {vergi_oncesi:>10,.2f} ₺")
        lines.append("")

        if toplam_indirilecek_yillik > 0:
            lines.append("─── SİGORTA PRİM İNDİRİMİ ───")
            if is_usd:
                lines.append(f"  Para Birimi: USD $ (Kur: {usd_kuru:.2f})")
            lines.append(f"  Yıllık Toplam İndirilebilir: {toplam_indirilecek_yillik:>12,.2f} ₺")
            lines.append(f"  Yıllık Uygulanan İndirim   : {indirim_uygulanacak_yillik:>12,.2f} ₺")
            lines.append("")
            
            lines.append("─── AYLARA GÖRE BORDROYA YANSIYAN İADE (NET MAAŞA ETKİSİ) ───")
            aylik_farklar = [] # (iade, oran) çiftleri
            kum_m_eski = 0
            
            for ay in range(1, 13):
                # Matrah
                prime_esas = min(brut_aylik, (asgari_ucret/12) * 7.5) if is_ucret else 0
                sgk_v_issizlik = prime_esas * 0.15 if is_ucret else 0
                matrah_aylik = brut_aylik - sgk_v_issizlik
                
                # İndirim
                ay_p = poli_aylik_matrahlar[ay-1]
                
                # Aylık ne kadarı iadeye konu olabilir? (Kalan yıllık limit kontrolü)
                uyg_aylik = min(ay_p, kalan_limit_yillik)
                kalan_limit_yillik -= uyg_aylik
                
                matrah_ay_ind = max(0, matrah_aylik - uyg_aylik)
                
                # Kümülatif hesap (Sadece vergi dilimi oranını tespit etmek için)
                yeni_kum_eski = kum_m_eski + matrah_aylik
                
                # O ayki marjinal vergi oranını bul (Mevcut kümülatif toplam üzerinden)
                aylik_oran = marjinal_vergi_orani(yeni_kum_eski, dilimler)
                
                # O ayki net iade = İndirim Tutarı * O ayki Vergi Oranı
                aylik_iade = uyg_aylik * aylik_oran
                aylik_farklar.append((aylik_iade, aylik_oran))
                
                kum_m_eski += matrah_aylik

            aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
            
            def add_monthly_table(subset_indices):
                # Üst Kenar
                top = "  " + "┌───────────────" * len(subset_indices) + "┐"
                lines.append(top)
                
                # Ay İsimleri
                names = "  "
                for idx in subset_indices:
                    names += f"│ {aylar[idx]:^13} "
                names += "│"
                lines.append(names)
                
                # Orta Ayraç
                mid = "  " + "├───────────────" * len(subset_indices) + "┤"
                lines.append(mid)
                
                # Değerler (İade + Vergi Dilimi)
                vals = "  "
                for idx in subset_indices:
                    iade, oran = aylik_farklar[idx]
                    oran_str = f"(%{oran*100:g})"
                    v_str = f"{iade:,.0f} ₺ {oran_str}"
                    vals += f"│ {v_str:^13} "
                vals += "│"
                lines.append(vals)
                
                # Alt Kenar
                bot = "  " + "└───────────────" * len(subset_indices) + "┘"
                lines.append(bot)

            # 4'erli gruplar halinde 3 satır tablo
            add_monthly_table([0, 1, 2, 3])
            lines.append("")
            add_monthly_table([4, 5, 6, 7])
            lines.append("")
            add_monthly_table([8, 9, 10, 11])
            lines.append("")

        # Sigorta türlerini dinamik topla
        policy_types = []
        for w in self.poli_widgets:
            ptype = w.tip_combo.currentText().split(" (")[0] # "Sağlık/Vefat" gibi
            if ptype not in policy_types:
                policy_types.append(ptype)
        
        # Sonuç verilerini bir sözlükte topla, tabloya da gönder
        result_data = {
            "toplam_prim": toplam_indirilecek_yillik,
            "vergi_iadesi": vergi_iadesi,
            "matrah_dusulen": indirim_uygulanacak_yillik,
            "brut_aylik": brut_aylik,
            "aylik_iade_listesi": aylik_farklar, # List[(iade, oran)]
            "ay_isimleri": aylar,
            "sigorta_turu": " / ".join(policy_types) if policy_types else "Belirtilmemiş",
            "vergi_dilimi": f"%{marjinal * 100:.0f}",
            "son_hesaplama": datetime.now().strftime("%d/%m/%Y"),
            "yil": CURRENT_YEAR
        }

        self.last_result_data = result_data
        self.result_text.setVisible(True)
        # Mevcut text özetini de ASCII olarak tutalım (panoya kopyalamak için)
        self.last_full_result = "\n".join(lines)
        self.result_text.setPlainText(self.last_full_result)
        self.details_btn.setVisible(True)
        
        # Sonuç detaylarını otomatik aç
        self._show_details_popup()

    def _show_details_popup(self):
        if hasattr(self, 'last_result_data'):
            dlg = ResultDetailsDialog(self, self.last_result_data)
            dlg.exec_()


# ──────────────────────────────────────────────
#  ANA PENCERE
# ──────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Finans Asistanı")
        self.setMinimumSize(720, 680)
        self.resize(800, 750)

        self.settings = load_settings()
        self.current_theme = self.settings.get("theme", "Okyanus")
        last_tab = self.settings.get("last_tab", 0)

        self.tabs = QTabWidget()
        self.tabs.addTab(CurrencyTab(self.settings), "💱 Kur Dönüşümü")
        self.tabs.addTab(PercentTab(), "📊 Yüzde Hesabı")
        self.tabs.addTab(TaxTab(self.settings), "🏛️ Vergi İadesi")
        self.tabs.setCurrentIndex(last_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.setCentralWidget(self.tabs)

        # Statusbar + tema seçici
        sb = self.statusBar()
        sb.showMessage("Hazır")

        self.btn_tax_settings = QPushButton("⚙️ Vergi Ayarları")
        self.btn_tax_settings.setObjectName("statusThemeBtn")
        self.btn_tax_settings.clicked.connect(self._open_tax_settings)
        self.btn_tax_settings.setVisible(False)
        sb.addPermanentWidget(self.btn_tax_settings)

        theme_label = QLabel("🎨 Tema:")
        theme_label.setStyleSheet("font-size: 11px; margin-left: 8px;")
        sb.addPermanentWidget(theme_label)

        self.theme_btn = QPushButton(self.current_theme)
        self.theme_btn.setFixedWidth(130)
        self.theme_btn.setStyleSheet(
            "font-size: 11px; padding: 2px 6px; max-height: 22px; text-align: left;"
        )
        self.theme_menu = QMenu(self)
        for name in THEMES:
            action = QAction(name, self)
            action.triggered.connect(lambda checked=False, n=name: self._apply_theme(n))
            self.theme_menu.addAction(action)

        self.theme_btn.clicked.connect(self._show_theme_menu)
        sb.addPermanentWidget(self.theme_btn)

    def _on_tab_changed(self, index):
        # 2. index Vergi İadesi sekmesi
        self.btn_tax_settings.setVisible(index == 2)
        
        # Son sekmeyi kaydet
        try:
            s = load_settings()
            s["last_tab"] = index
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(s, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _show_theme_menu(self):
        # Menü yüklendiğinde boyutunu hesapla
        self.theme_menu.adjustSize()
        # Butonun sol üst köşesinin global koordinatını al
        pos = self.theme_btn.mapToGlobal(self.theme_btn.rect().topLeft())
        # Menünün yüksekliği kadar yukarı kaydır (böylece tam üstünde açılır, programdan taşmaz)
        pos.setY(pos.y() - self.theme_menu.sizeHint().height())
        self.theme_menu.popup(pos)

    def _apply_theme(self, name: str):
        if hasattr(self, 'theme_btn'):
            self.theme_btn.setText(name)
        t = THEMES.get(name)
        if not t:
            return
        self.current_theme = name
        app = QApplication.instance()
        app.setStyleSheet(generate_style(t))
        app.setPalette(get_palette(t))
        try:
            s = load_settings()
            s["theme"] = name
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(s, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _open_tax_settings(self):
        dlg = TaxSettingsDialog(self, self.settings.get("tax_settings", {}))
        if dlg.exec_() == QDialog.Accepted:
            self.settings["tax_settings"] = dlg.get_settings()
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Bilgi", "Vergi ayarları güncellendi. Yeni hesaplamalar bu verilere göre yapılacaktır.")


class TaxSettingsDialog(QDialog):
    def __init__(self, parent, tax_settings):
        super().__init__(parent)
        self.setWindowTitle(f"Vergi Ayarları ({CURRENT_YEAR})")
        self.resize(550, 600)
        
        self.tax_settings = tax_settings
        
        layout = QVBoxLayout(self)
        
        # Asgari Ucret
        hl = QHBoxLayout()
        hl.addWidget(QLabel("Yıllık Brüt Asgari Ücret (₺):"))
        self.asgari_ucret_input = QLineEdit(str(self.tax_settings.get("asgari_ucret_yillik", 396360.0)))
        hl.addWidget(self.asgari_ucret_input)
        layout.addLayout(hl)
        
        def create_table(title, dilim_key):
            layout.addWidget(QLabel(title))
            table = QTableWidget(5, 2)
            table.setHorizontalHeaderLabels(["Üst Sınır (₺)", "Vergi Oranı (%)"])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            for i, (ust, oran) in enumerate(self.tax_settings.get(dilim_key, [])):
                ust_txt = "Limitsiz" if ust > 1e11 else f"{ust:.2f}"
                table.setItem(i, 0, QTableWidgetItem(ust_txt))
                table.setItem(i, 1, QTableWidgetItem(f"{oran * 100:.2f}"))
            layout.addWidget(table)
            return table

        self.table_ucret = create_table("ÜCRET Gelirleri İçin Vergi Dilimleri", "ucret_dilimleri")
        self.table_ucret_disi = create_table("ÜCRET DIŞI Gelirler İçin Vergi Dilimleri", "ucret_disi_dilimleri")
        
        bl = QHBoxLayout()
        btn_save = QPushButton("Kaydet")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("İptal")
        btn_cancel.clicked.connect(self.reject)
        bl.addWidget(btn_save)
        bl.addWidget(btn_cancel)
        layout.addLayout(bl)
        
    def get_settings(self):
        new_s = {}
        try:
            new_s["asgari_ucret_yillik"] = float(self.asgari_ucret_input.text().replace(',', '.'))
        except:
            new_s["asgari_ucret_yillik"] = 396360.0
            
        def read_table(table):
            arr = []
            for i in range(table.rowCount()):
                try:
                    ust_txt = table.item(i, 0).text()
                    if ust_txt.lower() in ["inf", "limitsiz", "sınırsız", "", "0"]:
                        ust = 9999999999.0
                    else:
                        ust = float(ust_txt.replace(',', '.'))
                        
                    oran = float(table.item(i, 1).text().replace(',', '.')) / 100.0
                    arr.append([ust, oran])
                except Exception:
                    pass
            return arr

        ucret = read_table(self.table_ucret)
        new_s["ucret_dilimleri"] = ucret if ucret else self.tax_settings.get("ucret_dilimleri", [])

        ucret_d = read_table(self.table_ucret_disi)
        new_s["ucret_disi_dilimleri"] = ucret_d if ucret_d else self.tax_settings.get("ucret_disi_dilimleri", [])
        
        return new_s


class ResultDetailsDialog(QDialog):
    """Görseldeki gibi modern dashboard içeren sonuç penceresi."""
    def __init__(self, parent, data):
        super().__init__(parent)
        self.setWindowTitle("Sigorta Primi Vergi İade Hesaplama")
        self.resize(900, 850)
        
        # Ana Layout (Koyu Arka Plan)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Üst Başlık (Görseldeki "2024 YILI ÖZETİ")
        title_lbl = QLabel(f"{data['yil']} YILI ÖZETİ")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(title_lbl)

        # Üst Bölüm: Bilgi Kartları ve Özet Bilgiler (H-Box)
        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)

        # 1. Kolon: Bilgi Kartları
        cards_layout = QVBoxLayout()
        cards_layout.setSpacing(10)
        
        def create_card(title, value):
            card = QFrame()
            card.setFrameShape(QFrame.StyledPanel)
            card.setMaximumHeight(100) # Özet kartları biraz daha ferah
            card.setStyleSheet("""
                QFrame {
                    background-color: #122d4f;
                    border: 1px solid #1e3a5f;
                    border-radius: 10px;
                }
            """)
            card_v = QVBoxLayout(card)
            card_v.setContentsMargins(10, 10, 10, 10)
            card_v.setSpacing(4)
            t_lbl = QLabel(title.upper())
            t_lbl.setStyleSheet("font-size: 10px; color: #a9d6e5; font-weight: bold;")
            v_lbl = QLabel(f"₺ {value:,.2f}")
            v_lbl.setStyleSheet("font-size: 19px; color: #ffffff; font-weight: bold;")
            card_v.addWidget(t_lbl)
            card_v.addWidget(v_lbl)
            return card

        cards_layout.addWidget(create_card("Toplam Prim Ödemesi", data['toplam_prim']))
        cards_layout.addWidget(create_card("Hak Edilen Vergi İadesi", data['vergi_iadesi']))
        cards_layout.addWidget(create_card("Matrahtan Düşülen Tutar", data['matrah_dusulen']))
        
        top_layout.addLayout(cards_layout, 1)

        # 2. Kolon: Grafik Alanı (Görselde grafik var)
        if HAS_CHART:
            self.chart_view = QChartView()
            self.chart_view.setRenderHint(QPainter.Antialiasing)
            self.chart_view.setStyleSheet("background-color: #0c1929; border: 1px solid #1e3a5f; border-radius: 12px;")
            self.chart_view.setMaximumHeight(320) # Grafik alanını büyüttük
            
            chart = QChart()
            chart.setBackgroundVisible(False)
            chart.setTitle("AYLIK VERGİ İADESİ VE PRİM DAĞILIMI")
            chart.setTitleFont(QFont("Arial", 10, QFont.Bold))
            chart.setTitleBrush(QColor("#a9d6e5"))
            
            # Veri setleri
            set_iade = QBarSet("Vergi İadesi (₺)")
            set_iade.setColor(QColor("#1b263b")) 
            set_iade.setBorderColor(QColor("#00d4ff"))
            
            line_series = QLineSeries()
            line_series.setName("İade Trendi (₺)")
            line_series.setColor(QColor("#00f5d4"))
            line_series.setPointsVisible(True) # Noktaları göster
            
            for i, (iade, oran) in enumerate(data['aylik_iade_listesi']):
                set_iade.append(iade)
                line_series.append(i, iade) # Sütunların tam ortasına (index i) denk gelir
                
            series = QBarSeries()
            series.append(set_iade)
            chart.addSeries(series)
            chart.addSeries(line_series)
            
            # Eksenler
            axis_x = QBarCategoryAxis()
            short_months = [m[:3] for m in data['ay_isimleri']]
            axis_x.append(short_months)
            axis_x.setLabelsBrush(QColor("#a9d6e5"))
            chart.addAxis(axis_x, Qt.AlignBottom)
            series.attachAxis(axis_x)
            line_series.attachAxis(axis_x)
            
            axis_y = QValueAxis()
            max_v = max([x[0] for x in data['aylik_iade_listesi']]) if data['aylik_iade_listesi'] else 1000
            axis_y.setRange(0, max_v * 1.3)
            axis_y.setLabelsBrush(QColor("#a9d6e5"))
            chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_y)
            line_series.attachAxis(axis_y)
            
            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignBottom)
            chart.legend().setLabelBrush(QColor("#a9d6e5"))
            
            self.chart_view.setChart(chart)
            top_layout.addWidget(self.chart_view, 2)
        else:
            graph_placeholder = QFrame()
            graph_placeholder.setStyleSheet("background-color: #0c1929; border: 1px solid #1e3a5f; border-radius: 12px;")
            graph_v = QVBoxLayout(graph_placeholder)
            graph_lbl = QLabel("Grafik Modülü Yüklü Değil (PyQtChart)")
            graph_lbl.setStyleSheet("font-size: 11px; color: #a9d6e5; font-weight: bold;")
            graph_lbl.setAlignment(Qt.AlignCenter)
            graph_v.addWidget(graph_lbl)
            graph_v.addStretch()
            top_layout.addWidget(graph_placeholder, 2)

        # 3. Kolon: Özet Bilgiler Paneli
        info_panel = QFrame()
        info_panel.setStyleSheet("background-color: #122d4f; border: 1px solid #1e3a5f; border-radius: 10px;")
        info_panel.setMaximumHeight(320) # Yan paneli grafik ile eşitledik
        info_v = QVBoxLayout(info_panel)
        info_v.setContentsMargins(15, 15, 15, 15)
        info_v.setSpacing(6)
        
        def add_info_row(title, value):
            t = QLabel(title.upper())
            t.setStyleSheet("font-size: 10px; color: #a9d6e5; font-weight: normal;")
            v = QLabel(value)
            v.setStyleSheet("font-size: 15px; color: #ffffff; font-weight: bold; margin-bottom: 4px;")
            info_v.addWidget(t)
            info_v.addWidget(v)

        add_info_row("Sigorta Türü", data['sigorta_turu'])
        add_info_row("Vergi Dilimi", data['vergi_dilimi'])
        add_info_row("Son Hesaplama", data['son_hesaplama'])
        info_v.addStretch()
        
        top_layout.addWidget(info_panel, 1)
        main_layout.addLayout(top_layout)

        # Orta Bölüm: Detay Tablosu
        table_lbl = QLabel("AYLIK PRİM VE VERGİ İADE DETAYLARI")
        table_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(table_lbl)

        self.table = QTableWidget(12, 5)
        self.table.setHorizontalHeaderLabels(["AY", "ÖDENEN PRİM (₺)", "MATRAH İNDİRİMİ (₺)", "VERGİ İADESİ (₺)", "DURUM"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setMinimumHeight(400) # Tabloyu daha büyük gösteriyoruz
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0c1929;
                color: #ffffff;
                border: 1px solid #1e3a5f;
                gridline-color: #1b263b;
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: #1b263b;
                color: #a9d6e5;
                padding: 6px;
                font-weight: bold;
                border: none;
            }
            QTableWidget::item { padding: 5px; }
        """)
        
        for i in range(12):
            iade, oran = data['aylik_iade_listesi'][i]
            self.table.setItem(i, 0, QTableWidgetItem(data['ay_isimleri'][i].upper()))
            # Bu demo verisidir - hesaplama mantığına göre basitleştirildi
            self.table.setItem(i, 1, QTableWidgetItem(f"{data['toplam_prim']/12:,.0f}"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{(iade/max(0.01,oran)):,.0f}"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{iade:,.0f}"))
            durum = "Ödendi" if i < datetime.now().month else "Bekliyor"
            self.table.setItem(i, 4, QTableWidgetItem(durum))
            
        main_layout.addWidget(self.table, 1) # Stretch ekledik

        # Alt Bölüm: Aksiyon Butonları (Yan yana)
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        
        btn_start = QPushButton("YENİ HESAPLAMA BAŞLAT")
        btn_start.setMinimumSize(250, 45)
        btn_start.setStyleSheet("background-color: #1a3f6f; color: #00d4ff; border: 1px solid #00d4ff;")
        btn_start.clicked.connect(self.close) # Pratik olarak pencereyi kapatır
        
        btn_export = QPushButton("📄 RAPORU DIŞA AKTAR")
        btn_export.setMinimumSize(250, 45)
        btn_export.clicked.connect(self._show_export_menu) # Menü açar
        
        bottom_layout.addWidget(btn_start)
        bottom_layout.addWidget(btn_export)
        main_layout.addLayout(bottom_layout)

    def _show_export_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #1b263b; color: #ffffff; border: 1px solid #1e3a5f; }
            QMenu::item:selected { background-color: #00d4ff; color: #000000; }
        """)
        
        act1 = QAction("🖼️ Resim Olarak Kaydet (PNG)", self)
        act1.triggered.connect(self._save_as_image)
        menu.addAction(act1)
        
        act2 = QAction("📄 PDF Belgesi Olarak Kaydet", self)
        act2.triggered.connect(self._save_as_pdf)
        menu.addAction(act2)
        
        act3 = QAction("📋 Metin Olarak Kopyala", self)
        act3.triggered.connect(self._copy_all)
        menu.addAction(act3)
        
        # Butonun üstünde aç
        pos = self.sender().mapToGlobal(self.sender().rect().topLeft())
        pos.setY(pos.y() - menu.sizeHint().height())
        menu.popup(pos)

    def _save_as_image(self):
        pixmap = self.grab() # Tüm pencerenin görüntüsünü alır
        path, _ = QFileDialog.getSaveFileName(self, "Raporu Kaydet", f"Vergi_İadesi_Raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.png", "Resim Dosyası (*.png)")
        if path:
            pixmap.save(path, "PNG")
            QMessageBox.information(self, "Başarılı", "Rapor resim olarak kaydedildi.")

    def _save_as_pdf(self):
        if not HAS_PRINTER:
            QMessageBox.warning(self, "Hata", "PDF çıktısı için gerekli bileşenler (QtPrintSupport) bulunamadı.")
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "Raporu Kaydet", f"Vergi_İadesi_Raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf", "PDF Dosyası (*.pdf)")
        if path:
            pixmap = self.grab()
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(path)
            printer.setPageMargins(10, 10, 10, 10, QPrinter.Millimeter)
            
            painter = QPainter(printer)
            # Pencereyi PDF sayfasına sığdır
            rect = painter.viewport()
            size = pixmap.size()
            size.scale(rect.size(), Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(pixmap.rect())
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            
            QMessageBox.information(self, "Başarılı", "Rapor PDF olarak kaydedildi.")

    def _copy_all(self):
        # Parent'ın sakladığı ASCII dökümü kopyala
        txt = self.parent().last_full_result if hasattr(self.parent(), 'last_full_result') else "Veri bulunamadı."
        QApplication.clipboard().setText(txt)
        QMessageBox.information(self, "Bilgi", "Hesaplama dökümü panoya kopyalandı.")


# ──────────────────────────────────────────────
#  BAŞLATICI
# ──────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    
    # Kayıtlı ayarları yükle
    settings = load_settings()
    
    app.setStyle("Fusion")

    # Temayı uygula
    theme_name = settings.get("theme", "Okyanus")
    t = THEMES.get(theme_name, THEMES["Okyanus"])
    app.setStyleSheet(generate_style(t))
    app.setPalette(get_palette(t))

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
