To prevent race conditions when creating payments,
row-level locking (SELECT FOR UPDATE) is used on the order.