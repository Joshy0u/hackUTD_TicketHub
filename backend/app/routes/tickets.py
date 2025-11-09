from flask import Blueprint, jsonify, request
from datetime import datetime
from PQ import Ticket, TicketQueue

tickets = Blueprint('tickets', __name__)
ticket_queue = TicketQueue()




@tickets.route('/open', methods=['POST'])
def upload_ticket():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    t = Ticket(
        priorityGiven=data.get('priorityGiven', 'Normal'),
        user=data.get('user', 'Anonymous'),
        desc=data.get('content', ''),
        estimatedPriority=int(data.get('estimatedPriority', 0))
    )

    ticket_queue.insert(t)

    return jsonify({'message': 'Ticket uploaded successfully'}), 201

@tickets.route('/', methods=['GET'])
def get_tickets():
    tickets_list = [
        {
            "priorityGiven": t[2].priorityGiven,
            "user": t[2].user,
            "desc": t[2].desc,
            "estimatedPriority": t[2].estimatedPriority
        }
        for t in ticket_queue.heap
    ]


    return jsonify(tickets_list), 200
