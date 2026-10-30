import json
import logging


class JsonFormatter(logging.Formatter):
    """One JSON object per log line, for log shippers (set LOG_FORMAT=json)."""

    def format(self, record):
        payload = {
            'time': self.formatTime(record, '%Y-%m-%dT%H:%M:%S'),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)
        return json.dumps(payload)
