select p.id product_id, pv.id variant_id, p.title, p.brand, pv.quantity_description, ph.event, p.created, ph.timestamp
from products p
INNER JOIN product_variants pv ON p.id = pv.product_id
INNER JOIN product_history ph ON p.id = ph.product_id AND pv.id = ph.variant_id
WHERE title = 'Toucher'
ORDER BY p.brand, p.title, p.id, pv.id, ph.timestamp;

SELECT p.title, p.brand, p.id product_id, p.in_stock product_in_stock, pv.id variant_id, pv.quantity_description, pv.in_stock variant_in_stock from products p
INNER JOIN product_variants pv ON p.id = pv.product_id
WHERE p.title = 'Pink Kush'