from flask import Blueprint, jsonify, request
from sqlalchemy import desc
from datetime import datetime
from ..database import get_db
from ..models import BadLog  # updated import

bad_logs = Blueprint('bad_logs', __name__)

@bad_logs.route('/logs', methods=['GET'])
def get_logs():
    """Get all logs, optionally filtered by label or hostname"""
    with get_db() as db:
        query = db.query(BadLog)

        # Optional filters
        label = request.args.get('label')
        hostname = request.args.get('hostname')

        if label:
            query = query.filter(BadLog.label == label)
        if hostname:
            query = query.filter(BadLog.hostname == hostname)

        # Order by most recent
        query = query.order_by(desc(BadLog.logged_at))

        logs = query.all()
        return jsonify([log.to_dict() for log in logs]), 200


@bad_logs.route('/logs/<int:log_id>', methods=['GET'])
def get_log(log_id):
    """Get a specific log entry by ID"""
    with get_db() as db:
        log = db.query(BadLog).filter(BadLog.id == log_id).first()
        if not log:
            return jsonify({'error': 'Log not found'}), 404
        return jsonify(log.to_dict()), 200


@bad_logs.route('/logs', methods=['POST'])
def create_log():
    """Create a new log entry"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Create new BadLog entry
    new_log = BadLog(
        uploadts=data.get('upload_ts'),
        hostname=data.get('hostname'),
        label=data.get('label'),
        log_line=data.get('log_line'),
    )

    with get_db() as db:
        db.add(new_log)
        db.flush()  # ensures ID is generated before commit
        return jsonify(new_log.to_dict()), 201


@bad_logs.route('/logs/<int:log_id>', methods=['PUT'])
def update_log(log_id):
    """Update an existing log"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    with get_db() as db:
        log = db.query(BadLog).filter(BadLog.id == log_id).first()
        if not log:
            return jsonify({'error': 'Log not found'}), 404

        # Update fields if provided
        if 'uploadts' in data:
            log.uploadts = data['uploadts']
        if 'hostname' in data:
            log.hostname = data['hostname']
        if 'label' in data:
            log.label = data['label']
        if 'log_line' in data:
            log.log_line = data['log_line']

        return jsonify(log.to_dict()), 200


@bad_logs.route('/logs/<int:log_id>', methods=['DELETE'])
def delete_log(log_id):
    """Delete a log entry"""
    with get_db() as db:
        log = db.query(BadLog).filter(BadLog.id == log_id).first()
        if not log:
            return jsonify({'error': 'Log not found'}), 404

        db.delete(log)
        return jsonify({'message': 'Log deleted successfully'}), 200
