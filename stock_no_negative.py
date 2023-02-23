#!/usr/bin/python3

import xmlrpc.client as client
import sys

username = 'miusuario' #the user
pwd = 'mipassword'      #the password of the user
db = 'midb'    #the database

url = 'http://localhost:8069'

common = client.ServerProxy('{}/xmlrpc/2/common'.format(url))
common.version()
uid = common.authenticate(db, username, pwd, {})

models = client.ServerProxy('{}/xmlrpc/2/object'.format(url))

print(uid)

quant_ids = models.execute_kw(db,uid,pwd,'stock.quant','search',[[('location_id.usage','=','internal'),('quantity','<',0)]])
print(len(quant_ids))
if len(quant_ids) == 0:
    print('No stock negative')
    sys.exit(4)
picking_type = models.execute_kw(db,uid,pwd,'stock.picking.type','search',[[('sequence_code','=','INT')]])
if not picking_type:
    print('No picking type')
    sys.exit(4)
loc_source_id = models.execute_kw(db,uid,pwd,'stock.location','search',[[('name','=','Inventory adjustment')]])
if not loc_source_id:
    print('No source location')
    sys.exit(4)
picking_type_data = models.execute_kw(db,uid,pwd,'stock.picking.type','read',picking_type)
vals_picking = {
    'picking_type_id': picking_type[0],
    'origin': 'Stock no negative',
    'location_id': loc_source_id[0],
    'location_dest_id': picking_type_data[0].get('default_location_dest_id')[0],
    }
picking_id = models.execute_kw(db,uid,pwd,'stock.picking','create',[vals_picking])

for quant_id in quant_ids:
    quant_data = models.execute_kw(db,uid,pwd,'stock.quant','read',[quant_id])
    quant_data = quant_data[0]
    print(quant_data.get('product_id'),quant_data.get('lot_id'),quant_data.get('quantity'))
    product_id = quant_data.get('product_id')[0]
    product_data = models.execute_kw(db,uid,pwd,'product.product','read',[product_id,['name','categ_id','uom_id']])
    product_data = product_data[0]
    print(product_data)
    vals = {}
    vals['picking_id'] = picking_id
    vals['product_id'] = product_id
    vals['location_dest_id'] = quant_data.get('location_id')[0]
    vals['product_uom'] = quant_data.get('product_uom_id')[0]
    vals['name'] = 'Update negative inventory %s' % product_data.get('name')
    vals['company_id'] = 1
    vals['state'] = 'draft'
    vals['product_uom_qty'] = abs(quant_data.get('quantity'))
    #vals['is_inventory'] = True
    # busca la ubicacion virtual de ajustes de inventario
    vals['location_id'] = loc_source_id[0]
    move_id = models.execute_kw(db,uid,pwd,'stock.move','create',[vals])
    print(move_id)
    # Agrega al diccionario el move_id y crea la línea de mov de stock
    vals['move_id'] = move_id
    # asigna la unidad de medida a product_uom_id y borra product_uom
    vals['product_uom_id'] = vals.get('product_uom')
    vals['qty_done'] = vals.get('product_uom_qty')
    if quant_data.get('lot_id'):
        vals['lot_id'] = quant_data.get('lot_id')[0]
    del vals['product_uom']
    # borra name
    del vals['name']
    move_line_id = models.execute_kw(db,uid,pwd,'stock.move.line','create',[vals])
    print(move_line_id)

