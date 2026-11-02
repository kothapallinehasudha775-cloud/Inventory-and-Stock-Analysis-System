"""Small unit tests for inventory calculation logic."""
def calculate_stock(opening_stock, transactions):
    stock = opening_stock
    for transaction_type, quantity in transactions:
        if transaction_type == "IN":
            stock += quantity
        elif transaction_type == "OUT":
            stock -= quantity
        elif transaction_type == "ADJUSTMENT":
            stock += quantity
    return stock


def test_stock_reconciliation():
    assert calculate_stock(10, [("IN", 5), ("OUT", 3)]) == 12


def test_adjustment_can_be_signed():
    assert calculate_stock(10, [("ADJUSTMENT", -2)]) == 8
