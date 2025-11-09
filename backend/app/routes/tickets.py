from flask import Blueprint, jsonify, request
from datetime import datetime
from ..database import get_db
from ..ticket_model import Ticket
from sqlalchemy import desc

tickets = Blueprint('tickets', __name__)

@tickets.route('/tickets', methods=['GET'])
def get_tickets():
    """Get all tickets, optionally filtered by priority or status"""
    with get_db() as db:
        query = db.query(Ticket)
        
        # Filter by priority if provided
        priority = request.args.get('priority')
        if priority:
            query = query.filter(Ticket.priorityGiven == priority)
            
        # Order by estimated priority (highest first)
        query = query.order_by(desc(Ticket.estimatedPriority))
        
        tickets_list = query.all()
        return jsonify([ticket.to_dict() for ticket in tickets_list]), 200

@tickets.route('/tickets/<int:ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    """Get a specific ticket by ID"""
    with get_db() as db:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        return jsonify(ticket.to_dict()), 200

@tickets.route('/tickets', methods=['POST'])
def create_ticket():
    """Create a new ticket"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Create new ticket
    new_ticket = Ticket(
        status='Open',  # Default status for new tickets
        title=data.get('title', 'Untitled'),
        desc=data.get('content', ''),  # Using 'content' as in original code
        user=data.get('user', 'Anonymous'),
        priorityGiven=data.get('priorityGiven', 'Normal'),
        estimatedPriority=int(data.get('estimatedPriority', 0))
    )
    
    # Save to database
    with get_db() as db:
        db.add(new_ticket)
        db.flush()  # Get the ID before commit
        return jsonify(new_ticket.to_dict()), 201

@tickets.route('/tickets/<int:ticket_id>', methods=['PUT'])
def update_ticket(ticket_id):
    """Update an existing ticket"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    with get_db() as db:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
            
        # Update fields if provided
        if 'status' in data:
            ticket.status = data['status']
        if 'priorityGiven' in data:
            ticket.priorityGiven = data['priorityGiven']
        if 'estimatedPriority' in data:
            ticket.estimatedPriority = int(data['estimatedPriority'])
        if 'content' in data:
            ticket.desc = data['content']
            
        return jsonify(ticket.to_dict()), 200

@tickets.route('/tickets/<int:ticket_id>', methods=['DELETE'])
def delete_ticket(ticket_id):
    """Delete a ticket"""
    with get_db() as db:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
            
        db.delete(ticket)
        return jsonify({'message': 'Ticket deleted successfully'}), 200
