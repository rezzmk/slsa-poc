from prometheus_client import start_http_server, Counter, Gauge
import time
import re
import subprocess

# Define metrics
SPAM_MESSAGES = Counter('spam_messages_total', 'Total number of spam messages detected')
SPAM_SCORE = Gauge('spam_score', 'SpamAssassin score of the last message', ['sender'])
MAIL_PROCESSED = Counter('mail_processed_total', 'Total number of emails processed')
HAM_MESSAGES = Counter('ham_messages_total', 'Total number of non-spam messages')

def parse_mail_log():
    """Parse mail log for spam scores"""
    try:
        log_output = subprocess.check_output(['tail', '-n', '100', '/var/log/mail.log'])
        log_lines = log_output.decode('utf-8').split('\n')
        
        for line in log_lines:
            if 'spamd' in line and 'identified spam' in line:
                SPAM_MESSAGES.inc()
                
                # Extract score and sender
                score_match = re.search(r'score=(\d+\.\d+)', line)
                sender_match = re.search(r'from=<(.+?)>', line)
                
                if score_match and sender_match:
                    score = float(score_match.group(1))
                    sender = sender_match.group(1)
                    SPAM_SCORE.labels(sender=sender).set(score)
            
            elif 'postfix' in line and 'status=sent' in line:
                MAIL_PROCESSED.inc()
                
    except Exception as e:
        print(f"Error parsing mail log: {e}")

def monitor_spam():
    """Main monitoring loop"""
    start_http_server(5000)
    
    while True:
        parse_mail_log()
        time.sleep(10)

if __name__ == '__main__':
    monitor_spam()
