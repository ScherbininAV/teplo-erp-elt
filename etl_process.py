import os
import pandas as pd
import warnings
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Блокировка мусорных логов
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# Подгрузка секретов из скрытого файла .env
load_dotenv()

class ETLPipeline:
    def __init__(self, source_file, target_file):
        self.source_file = source_file
        self.target_file = target_file
        
        # Безопасный перехват пароля
        db_password = os.getenv('DB_PASSWORD')
        if not db_password:
            raise ValueError("КРИТИЧЕСКАЯ ОШИБКА: Пароль БД не найден в системе.")
            
        self.engine = create_engine(f'postgresql://postgres:{db_password}@localhost:5432/teplo_erp')
        self.raw_catalog = None
        self.raw_sales = None
        self.clean_catalog = None
        self.clean_sales = None

    def extract(self):
        print("1. Extract (Извлечение из Excel)...")
        self.raw_catalog = pd.read_excel(self.source_file, sheet_name='Каталог SKU (Прайс)')
        self.raw_sales = pd.read_excel(self.source_file, sheet_name='Журнал продаж')

    def transform(self):
        print("2. Transform (Маппинг под схему БД)...")
        catalog = self.raw_catalog.dropna(subset=['SKU_ID']).copy()
        self.clean_catalog = pd.DataFrame({
            'sku_id': catalog['SKU_ID'],
            'sku_name': catalog['Наименование SKU'],
            'color': catalog['Цвет'],
            'aroma': catalog['Аромат'],
            'cost_price': pd.to_numeric(catalog['С/С 1 шт (Ручной ввод из Калькулятора)'], errors='coerce').fillna(0)
        })

        sales = self.raw_sales.dropna(subset=['Товар (SKU)']).copy()
        self.clean_sales = pd.DataFrame({
            'sale_date': pd.to_datetime(sales['Дата'], errors='coerce', format='%d.%m.%Y'),
            'sales_channel': sales['Канал продаж'],
            'sku_id': sales['Товар (SKU)'],
            'quantity': pd.to_numeric(sales['Кол-во (шт)'], errors='coerce').fillna(0),
            'actual_price': pd.to_numeric(sales['Фактическая Цена 1 шт (₽)'], errors='coerce').fillna(0),
            'marketplace_fee_percent': pd.to_numeric(sales['Комиссия МП (%)'], errors='coerce').fillna(0),
            'logistics_cost': pd.to_numeric(sales['Логистика/Доставка (₽)'], errors='coerce').fillna(0)
        })

    def load_to_db(self):
        print("3. Load (Идемпотентная запись в PostgreSQL)...")
        with self.engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE sales_journal, sku_catalog RESTART IDENTITY CASCADE;"))
            self.clean_catalog.to_sql('sku_catalog', con=conn, if_exists='append', index=False)
            self.clean_sales.to_sql('sales_journal', con=conn, if_exists='append', index=False)

    def extract_view(self):
        print("4. Export (Выгрузка готового дашборда)...")
        dashboard_df = pd.read_sql("SELECT * FROM v_unit_economics", con=self.engine)
        dashboard_df.to_excel(self.target_file, index=False)
        print(f"   -> УСПЕХ: Файл {self.target_file} сформирован.")

    def run(self):
        print("--- СТАРТ ELT КОНВЕЙЕРА ---")
        self.extract()
        self.transform()
        self.load_to_db()
        self.extract_view()
        print("--- ELT КОНВЕЙЕР УСПЕШНО ЗАВЕРШЕН ---\n")

if __name__ == "__main__":
    # Вызов конвейера без передачи пароля в явном виде
    pipeline = ETLPipeline(source_file='data.xlsx', target_file='final_dashboard.xlsx')
    pipeline.run()