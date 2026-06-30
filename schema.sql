-- Таблица 1: Справочник товаров (Dimension Table)
CREATE TABLE sku_catalog (
    sku_id VARCHAR(255) PRIMARY KEY,
    sku_name VARCHAR(255) NOT NULL,
    color VARCHAR(100),
    aroma VARCHAR(100),
    cost_price NUMERIC(10, 2) NOT NULL
);

-- Таблица 2: Журнал транзакций (Fact Table)
CREATE TABLE sales_journal (
    transaction_id SERIAL PRIMARY KEY,
    sale_date DATE,
    sales_channel VARCHAR(100),
    sku_id VARCHAR(255) REFERENCES sku_catalog(sku_id),
    quantity INTEGER NOT NULL DEFAULT 0,
    actual_price NUMERIC(10, 2) NOT NULL DEFAULT 0,
    marketplace_fee_percent NUMERIC(5, 2) DEFAULT 0,
    logistics_cost NUMERIC(10, 2) DEFAULT 0
);

-- Аналитическая витрина (ELT Transform Layer)
CREATE OR REPLACE VIEW v_unit_economics AS
SELECT 
    sj.transaction_id,
    sj.sale_date,
    sj.sales_channel,
    sj.sku_id,           
    sc.sku_name,         
    sc.color,            
    sc.aroma,            
    sj.quantity,
    sj.actual_price,
    (sj.quantity * sj.actual_price) AS revenue,
    sc.cost_price AS unit_cost,
    (sj.quantity * sc.cost_price) AS total_cost,
    (sj.quantity * sj.actual_price * sj.marketplace_fee_percent) AS marketplace_fee,
    sj.logistics_cost,
    ((sj.quantity * sj.actual_price) 
     - (sj.quantity * sc.cost_price) 
     - (sj.quantity * sj.actual_price * sj.marketplace_fee_percent)
     - sj.logistics_cost) AS net_profit
FROM 
    sales_journal sj
LEFT JOIN 
    sku_catalog sc ON sj.sku_id = sc.sku_id;