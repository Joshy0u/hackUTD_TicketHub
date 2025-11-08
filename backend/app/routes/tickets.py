from flask import Blueprint, jsonify, request

tickets = Blueprint('tickets', __name__)

open_tickets = [
    {
        'id': 1,
        'content': 'stuff',
        'priority': 100
    },
    {
        'id': 2,
        'content': 'more stuff',
        'priority': 50
    }
]

@tickets.route('/open', methods=['POST'])
def upload_ticket():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    open_tickets.append({
        'id': len(open_tickets) + 1,
        'content': data.get('content'),
        'priority': data.get('priority')
    })

    return jsonify({'message': 'Ticket uploaded successfully'}), 201

@tickets.route('/', methods=['GET'])
def get_tickets():
    return jsonify(open_tickets), 200
