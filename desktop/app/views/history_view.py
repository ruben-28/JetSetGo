from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from pathlib import Path
from datetime import datetime

# --- Matplotlib (Qt Canvas) ---
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

plt.style.use("dark_background")


class SpendingChart(QWidget):
    """Widget affichant les dépenses de l'année en cours (Jan-Déc)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.figure = Figure(figsize=(6, 3), dpi=100, facecolor="#00000000")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background: transparent;")
        self.layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)
        self.ax.patch.set_alpha(0)
        self.ax.set_facecolor("none")

    def update_chart(self, bookings):
        self.ax.clear()

        now = datetime.now()
        current_year = now.year

        monthly_totals = {m: 0 for m in range(1, 13)}

        if bookings:
            for b in bookings:
                date_str = b.get("check_in") or b.get("depart_date") or ""
                price = b.get("price", 0)

                if date_str and len(date_str) >= 7:
                    try:
                        dt = datetime.strptime(date_str[:7], "%Y-%m")
                        if dt.year == current_year:
                            monthly_totals[dt.month] += price
                    except ValueError:
                        continue

        x_indices = range(12)
        values = [monthly_totals[m] for m in range(1, 13)]

        labels = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
                  "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]

        colors = ["#0077b6"] * 12

        bars = self.ax.bar(x_indices, values, color=colors, width=0.6, zorder=3)

        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.spines["left"].set_visible(False)
        self.ax.spines["bottom"].set_color("#404040")

        self.ax.yaxis.set_visible(False)
        self.ax.grid(axis="y", color="white", alpha=0.05, linestyle="-", zorder=0)

        self.ax.set_xticks(list(x_indices))
        self.ax.set_xticklabels(labels, fontsize=9, color="#aaaaaa")
        self.ax.tick_params(axis="x", colors="#404040", length=0)

        max_val = max(values) if values and max(values) > 0 else 100
        for bar, val in zip(bars, values):
            if val > 0:
                height = bar.get_height()
                self.ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    height + (max_val * 0.02),
                    f"{int(val)}€",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    fontweight="bold",
                    color="#57606a",
                )

        self.figure.tight_layout()
        self.canvas.draw()


class BudgetChart(QWidget):
    """Widget affichant la répartition du budget (donut chart)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.figure = Figure(figsize=(5, 3), dpi=100, facecolor="#00000000")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background: transparent;")
        self.layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)
        self.ax.axis("equal")

    def update_chart(self, bookings):
        self.ax.clear()

        if not bookings:
            self.canvas.draw()
            return

        categories = {"FLIGHT": 0, "HOTEL": 0, "PACKAGE": 0}
        labels_map = {"FLIGHT": "Vols", "HOTEL": "Hôtels", "PACKAGE": "Packages"}
        colors_map = {"FLIGHT": "#0077b6", "HOTEL": "#ff6b35", "PACKAGE": "#9333ea"}

        total_spent = 0
        for b in bookings:
            b_type = b.get("booking_type", "FLIGHT")
            price = b.get("price", 0)
            if b_type in categories:
                categories[b_type] += price
                total_spent += price

        data, labels, colors = [], [], []
        for cat, amount in categories.items():
            if amount > 0:
                data.append(amount)
                labels.append(f"{labels_map[cat]}\n{amount:.0f}€")
                colors.append(colors_map[cat])

        if not data:
            self.canvas.draw()
            return

        wedges, texts, autotexts = self.ax.pie(
            data,
            labels=labels,
            colors=colors,
            autopct="%1.1f%%",
            startangle=90,
            pctdistance=0.85,
            wedgeprops=dict(width=0.3, edgecolor="white", linewidth=1),
        )

        plt.setp(texts, color="black", fontweight="bold", fontsize=9)
        plt.setp(autotexts, size=8, weight="bold", color="black")

        self.ax.text(
            0, 0,
            f"Total\n{total_spent:.0f} €",
            ha="center", va="center",
            fontsize=12, color="black", fontweight="bold",
        )

        self.canvas.draw()


class BookingCard(QFrame):
    clicked = Signal(dict)

    def __init__(self, booking: dict):
        super().__init__()
        self.booking = booking
        self.setObjectName("bookingCard")
        self.setCursor(Qt.PointingHandCursor)

        self.setStyleSheet("""
            QFrame#bookingCard {
                background: rgba(220, 224, 228, 0.6);
                border: 1px solid rgba(100, 100, 100, 0.1);
                border-radius: 16px;
                padding: 0px;
            }
            QFrame#bookingCard:hover {
                background: rgba(230, 234, 238, 0.8);
                border: 1px solid rgba(0, 153, 255, 0.3);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(10)

        booking_type = booking.get("booking_type", "FLIGHT")
        type_info = self._get_type_info(booking_type)

        type_badge = QLabel(type_info["label"])
        type_badge.setStyleSheet(f"""
            background: {type_info["color"]};
            color: white;
            padding: 6px 14px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 12px;
        """)
        header.addWidget(type_badge)

        header.addStretch()

        status = booking.get("status", "UNKNOWN")
        status_badge = QLabel(status.upper())
        status_color = "#22c55e" if status == "CONFIRMED" else "#ef4444"
        status_badge.setStyleSheet(f"""
            background: rgba(255, 255, 255, 0.9);
            color: {status_color};
            padding: 6px 14px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 11px;
            border: 2px solid {status_color};
        """)
        header.addWidget(status_badge)

        layout.addLayout(header)

        destination = self._get_destination_text(booking)
        dest_label = QLabel(destination)
        dest_label.setStyleSheet("""
            color: #0077b6;
            font-size: 20px;
            font-weight: 700;
            background: transparent;
        """)
        dest_label.setWordWrap(True)
        layout.addWidget(dest_label)

        details_grid = QGridLayout()
        details_grid.setSpacing(12)
        details_grid.setContentsMargins(0, 8, 0, 0)

        row = 0

        departure = self._get_departure_text(booking)
        if departure and departure != "—":
            self._add_detail_row(details_grid, row, "📍 Départ", departure)
            row += 1

        date = self._get_date_text(booking)
        if date:
            self._add_detail_row(details_grid, row, "📅 Date", date)
            row += 1

        price = booking.get("price", 0)
        self._add_detail_row(details_grid, row, "💰 Prix", f"{price:.2f} €")
        row += 1

        booking_id = (booking.get("id", "")[:12] + "...") if booking.get("id") else "—"
        id_label = QLabel(f"ID: {booking_id}")
        id_label.setStyleSheet("""
            color: #57606a;
            font-size: 11px;
            background: transparent;
        """)
        details_grid.addWidget(id_label, row, 0, 1, 2)

        layout.addLayout(details_grid)

    def _get_type_info(self, booking_type: str) -> dict:
        types = {
            "FLIGHT": {"label": "✈️ VOL", "color": "#0077b6"},
            "HOTEL": {"label": "🏨 HÔTEL", "color": "#ff6b35"},
            "PACKAGE": {"label": "📦 PACKAGE", "color": "#9333ea"},
        }
        return types.get(booking_type, {"label": booking_type, "color": "#6b7280"})

    def _get_destination_text(self, booking: dict) -> str:
        booking_type = booking.get("booking_type", "FLIGHT")
        if booking_type == "HOTEL":
            hotel_name = booking.get("hotel_name", "")
            hotel_city = booking.get("hotel_city", "")
            return f"{hotel_name}" if hotel_name else hotel_city
        elif booking_type == "PACKAGE":
            dest = booking.get("destination", "")
            hotel_name = booking.get("hotel_name", "")
            return f"{dest} - {hotel_name}" if hotel_name else dest
        return booking.get("destination", "Destination inconnue")

    def _get_departure_text(self, booking: dict) -> str:
        if booking.get("booking_type", "FLIGHT") == "HOTEL":
            return "—"
        return booking.get("departure", "")

    def _get_date_text(self, booking: dict) -> str:
        if booking.get("booking_type", "FLIGHT") == "HOTEL":
            return booking.get("check_in", "")
        return booking.get("depart_date", "")

    def _add_detail_row(self, grid: QGridLayout, row: int, label: str, value: str):
        label_widget = QLabel(label)
        label_widget.setStyleSheet("""
            color: #57606a;
            font-size: 13px;
            font-weight: 600;
            background: transparent;
        """)

        value_widget = QLabel(value)
        value_widget.setStyleSheet("""
            color: #24292f;
            font-size: 13px;
            font-weight: 600;
            background: transparent;
        """)

        grid.addWidget(label_widget, row, 0, Qt.AlignLeft)
        grid.addWidget(value_widget, row, 1, Qt.AlignRight)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.booking)
        super().mousePressEvent(event)


class HistoryView(QWidget):
    """
    Vue 'Mes Voyages' :
    - garde une liste locale self._bookings
    - add_booking() / remove_booking() => refresh auto (graphs + cards)
    """

    def __init__(self):
        super().__init__()
        self._bookings = []  # ✅ source unique pour l'écran

        self.setWindowTitle("JetSetGo - Mes Voyages")

        icon_path = Path(__file__).parent.parent.parent / "assets" / "logo.jpg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.resize(1400, 900)
        self.setObjectName("centralWidget")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(25)

        header = QHBoxLayout()
        header.setSpacing(20)

        logo_title = QLabel('JetSet<span style="color: #ff6b35;">Go</span>')
        logo_title.setObjectName("appTitle")
        logo_title.setTextFormat(Qt.RichText)
        header.addWidget(logo_title)

        header.addStretch()

        self.back_btn = QPushButton("← Retour à la recherche")
        self.back_btn.setObjectName("secondary")
        self.back_btn.setMinimumHeight(40)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.back_btn)

        main_layout.addLayout(header)

        title_row = QHBoxLayout()

        title = QLabel("Mes Voyages")
        title.setStyleSheet("color: #0077b6; font-size: 28px; font-weight: 700; background: transparent;")
        title_row.addWidget(title)

        title_row.addStretch()

        self.status = QLabel("")
        self.status.setStyleSheet("""
            color: #57606a;
            font-size: 15px;
            font-weight: 600;
            background: rgba(200, 205, 211, 0.5);
            padding: 8px 16px;
            border-radius: 8px;
        """)
        title_row.addWidget(self.status)

        main_layout.addLayout(title_row)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        chart_container = QFrame()
        chart_container.setStyleSheet("""
            background: rgba(255, 255, 255, 0.5);
            border-radius: 16px;
            border: 1px solid rgba(0,0,0,0.05);
        """)
        chart_container.setFixedWidth(520)

        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(10, 15, 10, 10)
        chart_layout.setSpacing(18)

        current_year = datetime.now().year
        spending_title = QLabel(f"📅 Dépenses {current_year}")
        spending_title.setStyleSheet("color: #57606a; font-weight: 700; font-size: 14px; background: transparent;")
        spending_title.setAlignment(Qt.AlignCenter)
        chart_layout.addWidget(spending_title)

        self.spending_chart = SpendingChart()
        chart_layout.addWidget(self.spending_chart)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: rgba(0,0,0,0.08);")
        chart_layout.addWidget(separator)

        budget_title = QLabel("📊 Répartition du Budget")
        budget_title.setStyleSheet("color: #57606a; font-weight: 700; font-size: 14px; background: transparent;")
        budget_title.setAlignment(Qt.AlignCenter)
        chart_layout.addWidget(budget_title)

        self.budget_chart = BudgetChart()
        chart_layout.addWidget(self.budget_chart)

        content_layout.addWidget(chart_container)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(16)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.addStretch()

        scroll.setWidget(self.cards_container)
        content_layout.addWidget(scroll, stretch=1)

        main_layout.addLayout(content_layout)

        # init UI vide
        self._refresh_ui()

    # =========================
    # API PUBLIC (pour ton Presenter)
    # =========================
    def set_bookings(self, bookings: list):
        """Remplace tout, puis refresh."""
        self._bookings = list(bookings) if bookings else []
        self._refresh_ui()

    def add_booking(self, booking: dict):
        """Ajout incremental => refresh auto."""
        if not booking:
            return
        self._bookings.append(booking)
        self._refresh_ui()

    def remove_booking_by_id(self, booking_id: str):
        """Optionnel: suppression => refresh auto."""
        if not booking_id:
            return
        self._bookings = [b for b in self._bookings if str(b.get("id")) != str(booking_id)]
        self._refresh_ui()

    # =========================
    # UI
    # =========================
    def set_status(self, text: str):
        self.status.setText(text)

    def show_error(self, message: str):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Erreur", message)

    def _refresh_ui(self):
        """1 seule fonction qui met à jour cards + graphs."""
        bookings = self._bookings

        # Update charts
        self.spending_chart.update_chart(bookings)
        self.budget_chart.update_chart(bookings)

        # Clear cards (keep stretch)
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if bookings:
            grid = QGridLayout()
            grid.setSpacing(16)

            for idx, booking in enumerate(bookings):
                card = BookingCard(booking)
                row = idx // 2
                col = idx % 2
                grid.addWidget(card, row, col)

            self.cards_layout.insertLayout(0, grid)
            self.set_status(f"🎫 {len(bookings)} réservation(s)")
        else:
            empty_label = QLabel("Aucune réservation trouvée")
            empty_label.setStyleSheet("""
                color: #57606a;
                font-size: 18px;
                font-weight: 600;
                background: transparent;
                padding: 60px;
            """)
            empty_label.setAlignment(Qt.AlignCenter)
            self.cards_layout.insertWidget(0, empty_label)
            self.set_status("0 réservation")
