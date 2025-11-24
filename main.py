import json
from pathlib import Path
from datetime import datetime

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen

from kivymd.app import MDApp
from kivymd.uix.list import OneLineListItem

# Optional: set window size on desktop for convenience
Window.size = (360, 640)


DATA_DIR = Path("data")
BILLS_FILE = DATA_DIR / "bills.json"


class MainScreen(Screen):
    pass


class CreateBillScreen(Screen):
    pass


class BillScreen(Screen):
    # placeholder for later: show details of a single bill
    bill_id = StringProperty("")


class AddItemScreen(Screen):
    pass


class GoodnightApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Indigo"
        # Ensure data dir exists and file exists
        DATA_DIR.mkdir(exist_ok=True)
        if not BILLS_FILE.exists():
            BILLS_FILE.write_text("[]", encoding="utf-8")

        # load KV automatically (goodnight.kv should exist)
        sm = ScreenManager()
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(CreateBillScreen(name="create_bill"))
        sm.add_widget(BillScreen(name="bill"))
        sm.add_widget(AddItemScreen(name="add_item"))
        # schedule population of list after UI built
        Clock.schedule_once(lambda dt: self.populate_bills(), 0.1)
        return sm

    # ---------- Data helpers ----------
    def load_bills(self):
        try:
            with BILLS_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    return []
                return data
        except Exception as e:
            print("Error loading bills:", e)
            return []

    def save_bills(self, bills):
        try:
            with BILLS_FILE.open("w", encoding="utf-8") as f:
                json.dump(bills, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Error saving bills:", e)

    def add_bill(self, title: str):
        title = title.strip() or "Без названия"
        bills = self.load_bills()
        new_bill = {
            "id": datetime.utcnow().strftime("%Y%m%d%H%M%S%f"),
            "title": title,
            "created_at": datetime.utcnow().isoformat(),
            "items": []  # позиции будут добавляться позже
        }
        bills.insert(0, new_bill)  # newest first
        self.save_bills(bills)
        return new_bill

    def add_item_to_bill(self, bill_id, title, price, person):
        bills = self.load_bills()
        for bill in bills:
            if bill["id"] == bill_id:
                bill["items"].append({
                    "title": title,
                    "price": float(price),
                    "person": person,
                })
                break
        self.save_bills(bills)

    # ---------- UI interaction ----------
    def populate_bills(self):
        """Fill the MDList on the MainScreen with bills from file."""
        try:
            main = self.root.get_screen("main")
            bills_list = main.ids.bills_list
            bills_list.clear_widgets()
            bills = self.load_bills()
            if not bills:
                bills_list.add_widget(OneLineListItem(text="Пока нет счетов"))
                return
            for bill in bills:
                title = bill.get("title", "Без названия")
                created = bill.get("created_at", "")
                # show short created date if possible
                if created:
                    try:
                        dt = datetime.fromisoformat(created)
                        created_str = dt.strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        created_str = created
                    label = f"{title} — {created_str}"
                else:
                    label = title
                item = OneLineListItem(text=label, on_release=lambda x, b=bill: self.open_bill(b))
                bills_list.add_widget(item)
        except Exception as e:
            print("populate_bills error:", e)

    def open_bill(self, bill):
        """Open bill screen (placeholder for now)."""
        # later we will pass bill id and show details
        self.root.current = "bill"
        self.populate_bill_items(bill)
        bill_screen = self.root.get_screen("bill")
        bill_screen.bill_id = bill.get("id", "")
        # temporarily set title label in KV using id
        try:
            bill_screen.ids.bill_title_label.text = bill.get("title", "Счёт")
        except Exception:
            pass

    def populate_bill_items(self, bill):
        bill_screen = self.root.get_screen("bill")
        items_list = bill_screen.ids.items_list
        items_list.clear_widgets()

        items = bill.get("items", [])
        if not items:
            items_list.add_widget(
                OneLineListItem(text="Нет позиций")
            )
            return

        for item in items:
            label = f"{item['title']} - {item['price']}р - {item['person']}"
            items_list.add_widget(OneLineListItem(text=label))

    def save_new_item(self):
        add_screen = self.root.get_screen("add_item")
        bill_id = add_screen.ids.bill_id_label.text

        title = add_screen.ids.item_title.text.strip()
        price = add_screen.ids.item_price.text.strip()
        person = add_screen.ids.item_person.text.strip()

        if not title or not price or not person:
            print("Ошибка: пустое поле")
            return

        self.add_item_to_bill(bill_id, title, price, person)

        #Очищаем форму
        add_screen.ids.item_title.text = ""
        add_screen.ids.item_price.text = ""
        add_screen.ids.item_person.text = ""

        #Возвращаемся на экран счета
        bills = self.load_bills()
        bill = next((b for b in bills if b["id"] == bill_id), None)

        if bill:
            self.open_bill(bill)

    def create_bill_from_ui(self):
        """Called from KV when user taps 'Создать' on CreateBillScreen."""
        try:
            create = self.root.get_screen("create_bill")
            title = create.ids.bill_title.text
            new_bill = self.add_bill(title)
            # clear input
            create.ids.bill_title.text = ""
            # go back to main and refresh list
            self.root.current = "main"
            Clock.schedule_once(lambda dt: self.populate_bills(), 0.05)
        except Exception as e:
            print("create_bill_from_ui error:", e)

    # Optional: back to main
    def go_main(self):
        self.root.current = "main"
        Clock.schedule_once(lambda dt: self.populate_bills(), 0.05)


if __name__ == "__main__":
    GoodnightApp().run()
