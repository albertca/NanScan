from PyQt4.QtCore import *
import wizard
import pooler

view_form_end = """<?xml version="1.0"?>
	<form string="Document queue scanned">
		<label align="0.0" string="The document queue has been scanned. Now you can verify the documents!" colspan="4"/>
	</form>"""

view_form_start = """<?xml version="1.0"?>
	<form string="Document queue update">
		<image name="gtk-info" size="64" colspan="2"/>
		<group colspan="2" col="4">
			<label align="0.0" string="All pending documents in the queue will be scanned." colspan="4"/>
			<label align="0.0" string="Note that this operation may take a lot of time, depending on the amount of documents." colspan="4"/>
			<label align="0.0" string="The following documents will be scanned:" colspan="4"/>
			<field name="documents" nolabel="1" colspan="4"/>
		</group>
	</form>"""

view_fields_start = {
	"documents": {'type':'text', 'string':'Documents', 'readonly':True}
}

class ScanDocumentQueueWizard(wizard.interface):
	def _before_scan(self, cr, uid, data, context):
		pool = pooler.get_pool(cr.dbname)
		obj = pool.get('nan.document')
		if 'ids' in data:
			ids = data['ids']
		else:
			ids = obj.search(cr, uid, [('state','=','pending')])
		values = obj.read(cr, uid, ids, ['name'])
		ret  = { 'documents': '\n'.join([x['name'] for x in values]) }
		return ret

	def _scan(self, cr, uid, data, context):
		pool = pooler.get_pool(cr.dbname)
		obj = pool.get('nan.document')
		if 'ids' in data:
			ids = data['ids']
		else:
			ids = obj.search(cr, uid, [('state','=','pending')])
		obj.scan_document(cr, uid, ids)
		return {}

	states = {
		'init': {
			'actions': [_before_scan],
			'result': {'type':'form', 'arch':view_form_start, 'fields': view_fields_start, 'state':[('end','Cancel','gtk-cancel'),('start','Start Scan','gtk-ok')]}
		},
		'start': {
			'actions': [_scan],
			'result': {'type':'form', 'arch':view_form_end, 'fields': {}, 'state':[('end','Close','gtk-close')]}
		}
	}
ScanDocumentQueueWizard('nan_document_scan')
