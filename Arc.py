import sys
import pandas as pd
import re
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTextEdit, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# 👉 استيراد الداتا من data.py
from data import DATA


class ItemManager:
    """Handles item logic"""
    def __init__(self, df):
        self.df = df

    def get_item_price(self, item_name):
        row = self.df[self.df['Name'].str.lower() == item_name.lower().strip()]
        if not row.empty:
            return row.iloc[0]['Sell Price']
        return 0

    def calculate_recycle_value(self, recycle_string):
        if pd.isna(recycle_string) or "Cannot be recycled" in str(recycle_string) or str(recycle_string).strip() in ["", "-"]:
            return 0, []

        total_value = 0
        components_list = []

        parts = str(recycle_string).split("\n")
        for part in parts:
            match = re.search(r'(\d+)x\s*(.+)', part)
            if match:
                qty = int(match.group(1))
                component_name = match.group(2).strip()

                price = self.get_item_price(component_name)
                total_value += qty * price

                components_list.append(f"{qty}x {component_name} ({price * qty:,.0f})")

        return total_value, components_list

    def get_recommendation(self, row, recycle_value):
        sell_price = row['Sell Price']
        keep_info = row['Keep for Quests/Workshop']

        if pd.notna(keep_info) and str(keep_info).strip() != "":
            return {
                "action": "KEEP",
                "icon": "🛡️",
                "reason": f"Needed for: {keep_info}"
            }

        if recycle_value > sell_price:
            profit = recycle_value - sell_price
            return {
                "action": "RECYCLE",
                "icon": "♻️",
                "reason": f"Recycling is more profitable (+{profit:,.0f} value)"
            }

        return {
            "action": "SELL",
            "icon": "💸",
            "reason": f"Selling directly is better (Recycle value: {recycle_value:,.0f})"
        }

    def search_item(self, query):
        results = self.df[self.df['Name'].str.contains(query, case=False, na=False)]

        if results.empty:
            return f"No items found matching: '{query}'."

        output = f"--- Search Results for: '{query}' ---\n\n"

        for _, row in results.iterrows():
            name = row['Name']
            sell_price = row['Sell Price']
            recycle_info = row['Recycles To']

            recycle_val, components = self.calculate_recycle_value(recycle_info)
            decision = self.get_recommendation(row, recycle_val)

            output += "="*50 + "\n"
            output += f"ITEM: {name.upper()}\n"
            output += "-" * 50 + "\n"
            output += f"💰 Direct Sell Price:  {sell_price:,.0f}\n"

            if components:
                output += f"🔧 Recycles Into:      {', '.join(components)}\n"
                output += f"📊 Total Recycle Val:  {recycle_val:,.0f}\n"
            else:
                output += f"🔧 Recycles Into:      Nothing / Cannot be recycled\n"

            output += "-" * 50 + "\n"
            output += f"💡 RECOMMENDATION:     {decision['icon']} {decision['action']}\n"
            output += f"📝 REASON:             {decision['reason']}\n"
            output += "="*50 + "\n\n"

        return output


class ItemManagerGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # 👉 تحميل الداتا مباشرة بدون CSV
        df = pd.DataFrame(DATA)
        df['Sell Price'] = (
            df['Sell Price']
            .astype(str)
            .str.replace(r'[",]', '', regex=True)
        )
        df['Sell Price'] = pd.to_numeric(df['Sell Price'], errors='coerce').fillna(0)
        df['Name'] = df['Name'].astype(str).str.strip()

        self.manager = ItemManager(df)

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Arc Raiders - Item Manager")
        self.setGeometry(100, 100, 900, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()

        # Title
        title = QLabel("Arc Raiders - ITEM MANAGER")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Search section
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search Item:"))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter item name...")
        self.search_input.returnPressed.connect(self.search)
        search_layout.addWidget(self.search_input)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.search)
        search_layout.addWidget(search_btn)
        main_layout.addLayout(search_layout)

        # Results display
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        results_font = QFont("Courier")
        results_font.setPointSize(10)
        self.results_text.setFont(results_font)
        main_layout.addWidget(self.results_text)

        central_widget.setLayout(main_layout)

        self.results_text.setText("✓ Data loaded! Enter an item name to search.")

    def search(self):
        query = self.search_input.text().strip()

        if not query:
            QMessageBox.warning(self, "Warning", "Please enter an item name.")
            return

        results = self.manager.search_item(query)
        self.results_text.setText(results)


def main():
    app = QApplication(sys.argv)
    window = ItemManagerGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
