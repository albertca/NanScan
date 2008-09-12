##############################################################################
#
# Copyright (c) 2008 Albert Cervera i Areny <albert@nan-tic.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from NaNScaN.template import *
import rpc
from widget.model.group import *

class TemplateStorageManager:
	@staticmethod
	def save(template):
		if template.id:
			rpc.session.call( '/object', 'execute', 'nan.template', 'write', [template.id], {'name': template.name } )
			ids = rpc.session.call( '/object', 'execute', 'nan.template.box', 'search', [('template_id','=',template.id)] )
			rpc.session.call( '/object', 'execute', 'nan.template.box', 'unlink', ids )
		else:
			template.id = rpc.session.call( '/object', 'execute', 'nan.template', 'create', {'name': template.name } )
		for x in template.boxes:
			values = { 
				'x': x.rect.x(), 
				'y': x.rect.y(), 
				'width': x.rect.width(), 
				'height': x.rect.height(), 
				'feature_x' : x.featureRect.x(),
				'feature_y' : x.featureRect.y(),
				'feature_width' : x.featureRect.width(),
				'feature_height' : x.featureRect.height(),
				'template_id': template.id, 
				'name': x.name, 
				'text': x.text, 
				'recognizer': x.recognizer, 
				'type': x.type, 
				'filter': x.filter 
			}
			rpc.session.call( '/object', 'execute', 'nan.template.box', 'create', values )
	
	@staticmethod
	def load(id):

		fields = rpc.session.execute('/object', 'execute', 'nan.template.box', 'fields_get')
		
		model.value('boxes').addFields( fields )
		for x in model.value('boxes'):
			box = TemplateBox()
			box.rect = QRectF( x.value('x'), x.value('y'), x.value('width'), x.value('height') )
			box.featureRect = QRectF( x.value('feature_x'), x.value('feature_y'), 
						  x.value('feature_width'), x.value('feature_height') )
			box.name = x.value('name')
			box.text = x.value('text')
			box.recognizer = x.value('recognizer')
			box.type = x.value('type')
			box.filter = x.value('filter')
			template.addBox( box )

	@staticmethod
	def loadAll():
		fields = ['name', 'boxes']
		templateFields = rpc.session.execute('/object', 'execute', 'nan.template', 'fields_get', fields)
		fields = ['x', 'y', 'width', 'height', 'feature_x', 'feature_y', 'feature_width', 
			'feature_height', 'name', 'text', 'recognizer', 'type', 'filter' ]
		boxFields = rpc.session.execute('/object', 'execute', 'nan.template.box', 'fields_get', fields)
		ids = rpc.session.execute('/object', 'execute', 'nan.template', 'search', [])
		group = ModelRecordGroup( 'nan.template', templateFields, ids )
		templates = []
		for record in group:
			template = Template( record.value('name') )	
			template.id = record.id
			record.value('boxes').addFields(boxFields)
			for boxRecord in record.value('boxes'):
				box = TemplateBox()
				box.rect = QRectF( boxRecord.value('x'), 
						boxRecord.value('y'), 
						boxRecord.value('width'), 
						boxRecord.value('height') )
				box.featureRect = QRectF( boxRecord.value('feature_x'), 
							boxRecord.value('feature_y'), 
							boxRecord.value('feature_width'), 
							boxRecord.value('feature_height') )
				box.name = boxRecord.value('name')
				box.text = boxRecord.value('text')
				box.recognizer = boxRecord.value('recognizer')
				box.type = boxRecord.value('type')
				box.filter = boxRecord.value('filter')
				template.addBox( box )
			templates.append( template )
		return templates

